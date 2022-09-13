from inspect import isclass
import re
import sys
'''
Format:

Names:
variable: [a-z] or \'[a-zA-Z_]+\'
function: [A-Z] or <[a-zA-Z_]+>
literal : {[a-z]:([^\\}]|[\\].)*}

Definition:
[A-Z] =
<[A-Z_]+> =
[A-Z]{[0-9]+} = <[0-9]+>
<[A-Z_]+>{[0-9]+} = <[0-9]+>
{[a-z]+} = {([^\\}]|[\\].)*<>([^\\}]|[\\].)*}
{[a-z]+:([^\\}]|[\\].)*} = {([^\\}]|[\\].)*<>([^\\}]|[\\].)*}
'''

variable = {'f', 'g', 'x', 'y', 'z'}
macro = {
    'N': 'KI',
    'T': 'CI',
    'M': 'SII',
    'V': 'BCT'
}
args = {
    'I': 1,
    'K': 2,
    'B': 3,
    'C': 3,
    'S': 3
}
_var = r'[a-z]|\'[a-zA-Z_]+\''
_func = r'[A-Z]|<[a-zA-Z_]+>'
_lit = r'{[a-z]+:([^\\}]|[\\].)*}'
_generic = r'[A-Z()]|<[a-zA-Z_]+>|{[a-z]+:([^\\}]|[\\].)*}'
_quant = r'{\d+}'
_fld = r'<\d+>'
_calc = r'{([^\\}]|[\\].)*<>([^\\}]|[\\].)*}'
_check = re.compile(
    r'{.*(import\s+os'
    r'|from\s+os\s+import).*}'
)
_type = re.compile(
    r'{[a-z]+(:([^\\}]|[\\].)*)?}'
)
_equation = re.compile(
    f'({_generic}|{_calc})+'
)
_name = re.compile(
    _func
)
_expression = re.compile(
    f'({_generic})+'
)
_function = re.compile(
    f'({_func}){_quant}'
)
_definition = re.compile(
    f'({_generic}|{_fld})+'
)
_variable = re.compile(
    r'[a-zA-Z_]+'
)
_macro = re.compile(
    r'<[a-zA-Z_]+>'
)
_literal = re.compile(
    _lit
)
_calculation = re.compile(
    f'({_calc})'
)
_field = re.compile(
    r'<(\d)>'
)
_slash = re.compile(
    r'(\\.)'
)


def calculate_init(var):
    def closure(string: re.Match):
        print(var)
        print(string.group())
        output = eval(
            _slash.sub(r'\1', string.group()[1:-1]).replace('<>', var), {}
        )
        return f'{{{output.__class__.__name__}:{repr(output)}}}'
    return closure


def _I(arg):
    return arg[0]


def _K(arg):
    return arg[0]


def _B(arg):
    print('B')
    print(arg)
    return '{0}({1}{2})'.format(*arg)


def _C(arg):
    print('C')
    print(arg)
    return '{0}{2}{1}'.format(*arg)


def _S(arg):
    print('S')
    print(arg)
    return '{0}{2}({1}{2})'.format(*arg)


_arguments = {
    'I': _I,
    'K': _K,
    'B': _B,
    'C': _C,
    'S': _S
}


def custom_func(value):
    def closure(arg):
        return value.format(*arg)
    return closure


def initialise(code: str, macros: list[str]=[]):
    '''initialise the compiler'''
    for x in macros:
        if x == '':
            continue
        y = x.split('=')
        assert len(y) == 2, f'macro {x} has {len(y) - 1} \'=\' instead 1'
        key = y[0].rstrip()
        value = y[1].lstrip().rstrip()
        if key[0] == '{':
            assert _type.fullmatch(key), f'macro ({x}) does not meet standards'
            assert not _check.search(key), f'macro ({x}) imports os module'
            assert not _check.search(value), f'macro ({x}) imports os module'
            keys = key[1:-1].split(':')
            assert _equation.fullmatch(value), f'macro ({x}) does not meet standards'
            if len(keys) == 2:
                if keys[0] in macro:
                    macro[keys[0]][keys[1]] = value
                else:
                    macro[keys[0]] = {keys[1]: value}
            else:
                assert isclass(x := eval(keys[0], {})), f'class ({x}) is not defined'
                macro[keys[0]] = {'': value}
            continue
        if _name.fullmatch(key):
            assert _expression.fullmatch(value), f'macro ({x}) does not meet standards'
            macro[key] = value
            continue
        assert _function.fullmatch(key), f'macro ({x}) does not meet standards'
        assert _definition.fullmatch(value), f'macro ({x}) does not meet standards'
        name, number = key[:-1].split('{')
        value.replace('{', '{{').replace('}', '}}')
        args[name] = int(number)
        value = _field.sub(r'{\1}', value)
        _arguments[name] = custom_func(value)
    code_lst = code.split('\'')
    for x in code_lst[::2]:
        for y in x:
            if y.islower():
                variable.add(y)
    for x in code_lst[1::2]:
        assert _variable.fullmatch(x), f'variable \'{x}\' contains non-lowercase characters'
        variable.add(x)
    assert len(code_lst) % 2 == 1, f'code {code} contains unmatched \''
    bra = code.count('(')
    ket = code.count(')')
    assert bra <= ket, f'code {code} contains unmatched ('
    assert bra >= ket, f'code {code} contains unmatched )'
    bra = code.count('{')
    ket = code.count('}')
    assert bra <= ket, f'code {code} contains unmatched {{'
    assert bra >= ket, f'code {code} contains unmatched }}'


def step(code: str):
    '''step forward'''
    bracket_flag = len(code)  # not 1st character
    for i, operator in enumerate(code):
        if bracket_flag:  # if inside a bracket
            macro_flag = False
            if operator == '(':  # brackets
                brackets = 1
                for index, y in enumerate(code[i + 1:], i + 1):
                    if y == '(':
                        brackets += 1
                    elif y == ')':
                        brackets -= 1
                    if brackets == 0:
                        end = index
                        break
                return code[:i] + code[i + 1:end] + code[end + 1:]

            if operator == '{':  # complex macro
                operator = _literal.match(code, i)
                cls, instance = operator.group()[1:-1].split(':')
                if instance in macro[cls]:
                    return code[:i] + macro[cls][instance] + code[operator.end():]
                definition: str = macro[cls]['']
                instance = repr(eval(cls)(instance))
                calculate = calculate_init(instance)
                return code[:i] + _calculation.sub(calculate, definition) + code[operator.end():]

            if operator == '<' :
                matched = _macro.match(code, i)
                if (operator := matched.group()) in macro:  # multiletter macro
                    return code[:i] + macro[operator] + code[matched.end():]
                macro_flag = True

            if operator.isupper():
                if operator in macro:  # macro
                    return code[:i] + macro[operator] + code[i + 1:]
                macro_flag = True

            if macro_flag:
                arguments = []
                end = i + 1
                for x in range(args[operator]):  # arguments
                    start = end
                    if start == bracket_flag:
                        break
                    char = code[start]
                    if char.isalnum():
                        end = start
                    elif char == '\'':
                        end = code.find('\'',  start + 1)
                    elif char == '<':
                        end = code.find('>',  start + 1)
                    elif char == '{':
                        end = code.find('}',  start + 1)
                    elif char == '(':
                        brackets = 1
                        for index, y in enumerate(code[start + 1:], start + 1):
                            if y == '(':
                                brackets += 1
                            elif y == ')':
                                brackets -= 1
                            if brackets == 0:
                                end = index
                                break
                    end += 1
                    arguments.append(code[start:end])
                else:
                    return code[:i] + _arguments[operator](arguments) + code[end:]

            bracket_flag = False
        else:  # if not just inside a bracket
            if operator == '(':  # brackets
                brackets = 1
                for index, y in enumerate(code[i + 1:], i + 1):
                    if y == '(':
                        brackets += 1
                    elif y == ')':
                        brackets -= 1
                    if brackets == 0:
                        bracket_flag = index
                        break
    return False


def analyse(code, macros=[]):
    '''analyse completely'''
    initialise(code, macros)
    while code:
    # for x in range(300):
        code = step(code)
        print(code)
        print()
        # if not code:
        #     break


def _main():
    string = 'BM(CBM)f'
    initialise(string)
    print(string)
    for x in range(10):
        string = step(string)
        print(string)
        if not string:
            break


if len(sys.argv) - 1:
    with open(sys.argv[1], 'r') as f:
        lines = f.readlines()
        string = lines[-1]
        analyse(string, [x[:-1] for x in lines[:-1]])
elif __name__ == '__main__':
    _main()
