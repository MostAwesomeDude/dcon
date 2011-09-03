from pymeta.grammar import OMeta

blog_grammar = """

doublecrlf ::= '\r' '\n' '\r' '\n' => "</p><p>"

crlf ::= '\r' '\n' => "<br />"

not_crlf ::= ~'\r' <anything>

double_star ::= '*' '*'

bold ::= <double_star> (~<double_star> <not_crlf>)+:b <double_star>
    => "<b>%s</b>" % "".join(b)

italics ::= '*' (~'*' <not_crlf>)+:i '*' => "<i>%s</i>" % "".join(i)

underline ::= '_' (~'_' <not_crlf>)+:u '_' => "<u>%s</u>" % "".join(u)

paragraphs ::=
    (<doublecrlf> | <crlf> | <bold> | <italics> | <underline> | <anything>)*:l
    => "<p>%s</p>" % "".join(l)

"""

class BlogGrammar(OMeta.makeGrammar(blog_grammar, globals())):
    pass
