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

crlfs ::= <doublecrlf> | <crlf>

decorations ::= <bold> | <italics> | <underline>

entities ::= <crlfs> | <decorations>

paragraphs ::= (<entities> | <anything>)*:l => "<p>%s</p>" % "".join(l)

"""

html_grammar = """

less_than ::= '<' => "&lt;"

greater_than ::= '>' => "&gt;"

ampersand ::= '&' => "&amp;"

safe_entities ::= <less_than> | <greater_than> | <ampersand>

safe_paragraphs ::= (<safe_entities> | <entities> | <anything>)*:l
    => "<p>%s</p>" % "".join(l)

"""

class BlogGrammar(OMeta.makeGrammar(blog_grammar + html_grammar, globals())):
    pass
