Y{1} = <0>(Y<0>)
N = KI
T = CI
M = SII
V = BCT
{bool:True} = K
{bool:False} = N
<not> = C(T{bool:False}){bool:True}
<pair> = V
<first> = T{bool:True}
<second> = T{bool:False}
<zero> = <first>
<next> = <pair>{bool:False}
<prev> = <second>
{int} = <next>{<>-1}
{int:0} = I
<add> = C<apply><next>
<apply> = Y(B(S(BB(BS<zero>)))(B(B(SB))(CB<prev>)))
<next_pair> = S(B<pair><second>)(S(<add><first>)<second>)
<fib> = C(B<first>(C<apply><next_pair>))(<pair>{int:0}(<next>{int:0}))

{int:3}