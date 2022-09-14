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
from inspect import isclass
import re
import sys
from typing import Any

variable = {'f', 'g', 'x', 'y', 'z'}
macro: dict[str, Any] = {
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
_useless_identity = re.compile(
    r'\(I\)'
)


def _calculate_init(var):
    def closure(function: re.Match):
        # pylint: disable=eval-used
        output = eval(
            _slash.sub(r'\1', function.group()[1:-1]).replace('<>', var), {}
        )
        return f'{{{output.__class__.__name__}:{repr(output)}}}'
    return closure


def _I(arg):
    return arg[0]


def _K(arg):
    return arg[0]


def _B(arg):
    return '{0}({1}{2})'.format(*arg)


def _C(arg):
    return '{0}{2}{1}'.format(*arg)


def _S(arg):
    return '{0}{2}({1}{2})'.format(*arg)


_arguments = {
    'I': _I,
    'K': _K,
    'B': _B,
    'C': _C,
    'S': _S
}


def _custom_func(value: str):
    def closure(arg: list[str]):
        return value.format(*arg)
    return closure


def _check_type(code: str, key: str, value: str):
    assert _type.fullmatch(key), f'macro ({code}) does not meet standards'
    assert not _check.search(key), f'macro ({code}) imports os module'
    assert not _check.search(value), f'macro ({code}) imports os module'
    keys = key[1:-1].split(':')
    assert _equation.fullmatch(value),\
        f'macro ({code}) does not meet standards'
    if len(keys) == 2:
        if keys[0] in macro:
            macro[keys[0]][keys[1]] = value
        else:
            macro[keys[0]] = {keys[1]: value}
    else:
        assert isclass(code := eval(keys[0], {})),\
            f'class ({code}) is not defined'  # pylint: disable=eval-used
        macro[keys[0]] = {'': value}


def _check_macro(code: str, key: str, value: str):
    assert _expression.fullmatch(value),\
        f'macro ({code}) does not meet standards'
    macro[key] = value


def _check_function(code: str, key: str, value: str):
    assert _function.fullmatch(key), f'macro ({code}) does not meet standards'
    assert _definition.fullmatch(value),\
        f'macro ({code}) does not meet standards'
    name, number = key[:-1].split('{')
    value.replace('{', '{{').replace('}', '}}')
    args[name] = int(number)
    value = _field.sub(r'{\1}', value)
    _arguments[name] = _custom_func(value)


def _end_of_bracket(code: str, start: int):
    brackets = 1
    for index, y in enumerate(code[start + 1:], start + 1):
        if y == '(':
            brackets += 1
        elif y == ')':
            brackets -= 1
        if brackets == 0:
            return index
    return -1


def _macro_operator(operator: str, code: str, start: int, end_bracket: int):
    arguments = []
    end = start + 1
    for _ in range(args[operator]):  # arguments
        start = end
        if start == end_bracket:
            break
        char = code[start]
        if char.isalnum():
            end = start
        elif char == '\'':
            end = code.find('\'', start + 1)
        elif char == '<':
            end = code.find('>', start + 1)
        elif char == '{':
            end = code.find('}', start + 1)
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
        print(operator)
        print(arguments)
        return _arguments[operator](arguments), end


def _literal_operator(code: str, start: int):
    literal = _literal.match(code, start)
    assert literal is not None
    cls, instance = literal.group()[1:-1].split(':')
    if instance in macro[cls]:
        return macro[cls][instance], literal.end()
    definition: str = macro[cls]['']
    instance = repr(eval(cls)(instance))  # pylint: disable=eval-used
    calculate = _calculate_init(instance)
    return _calculation.sub(calculate, definition), literal.end()


def evaluate(code: str):
    '''evaluates code'''
    bracket_flag = len(code)  # not 1st character
    result = ''
    for i, operator in enumerate(code):
        if bracket_flag:  # if inside a bracket
            if operator == '(':  # brackets
                end = _end_of_bracket(code, i) + 1
                result = code[i + 1:end - 1]

            elif operator == '{':  # complex macro
                result, end = _literal_operator(code, i)

            elif operator == '<':
                matched = _macro.match(code, i)
                assert matched is not None
                if (operator := matched.group()) in macro:  # multiletter macro
                    result = macro[operator]
                    end = matched.end()
                else:
                    if (c := _macro_operator(operator, code, i, bracket_flag))\
                            is not None:
                        result, end = c

            elif operator.isupper():
                if operator in macro:  # macro
                    result = macro[operator]
                    end = i + 1
                else:
                    if (c := _macro_operator(operator, code, i, bracket_flag))\
                            is not None:
                        result, end = c

            if result:
                return code[:i] + result + code[end:]

            bracket_flag = False
        else:  # if not just inside a bracket
            if operator == '(':
                bracket_flag = _end_of_bracket(code, i)
    return None


def expand(code: str):
    '''expand code'''
    bracket_flag = True
    result = ''
    for i, operator in enumerate(code):
        if operator == '{':  # complex macro
            result, end = _literal_operator(code, i)

        elif operator == '<':
            matched = _macro.match(code, i)
            assert matched is not None
            if (operator := matched.group()) in macro:  # multiletter macro
                result = macro[operator]
                end = code[matched.end()]

        elif operator.isupper():
            if operator in macro:  # macro
                result = macro[operator]
                end = i + 1

        if result:
            return f'{code[:i]}({result}){code[end:]}'

        if operator == '(':  # brackets
            if bracket_flag:
                end = _end_of_bracket(code, i)
                return code[:i] + code[i + 1:end] + code[end + 1:]
            bracket_flag = True
        else:
            bracket_flag = False
    return None


def initialise(code: str, macros: list[str] = None):
    '''initialise the compiler'''
    if macros is None:
        macros = []
    for x in macros:
        if x == '':
            continue
        y = x.split('=')
        assert len(y) == 2, f'macro {x} has {len(y) - 1} \'=\' instead 1'
        key = y[0].rstrip()
        value = y[1].lstrip().rstrip()
        if key[0] == '{':
            _check_type(x, key, value)
            continue
        if _name.fullmatch(key):
            _check_macro(x, key, value)
            continue
        _check_function(x, key, value)
    assert not _check.search(code), f'code ({code}) imports os module'
    code_lst = code.split('\'')
    for z in code_lst[::2]:
        for x in z:
            if x.islower():
                variable.add(x)
    for x in code_lst[1::2]:
        assert _variable.fullmatch(x),\
            f'variable \'{x}\' contains non-lowercase characters'
        variable.add(x)
    assert len(code_lst) % 2 == 1, f'code {code} contains unmatched \''
    code = _slash.sub('', code)
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
    if (result := evaluate(code)) is not None:
        return result

    if (result := expand(code)) is not None:
        return result

    if _useless_identity.search(code):
        return _useless_identity.sub(r'I', code)
    return False


def analyse(code, macros=None):
    '''analyse completely'''
    initialise(code, macros)
    a = code
    # for x in range(300):
    while a:
        code = a
        a = step(code)
        print(a)
        print()
        # if not a:
        #     break


def _main():
    string = 'BM(CBM)f'  # pylint: disable=redefined-outer-name
    initialise(string)
    print(string)
    for _ in range(10):
        string = step(string)
        print(string)
        if not string:
            break


if len(sys.argv) - 1:
    with open(sys.argv[1], 'r', encoding="utf-8") as f:
        lines = f.readlines()
        string = lines[-1]
        analyse(string, [x[:-1] for x in lines[:-1]])
elif __name__ == '__main__':
    _main()
