from pymeta.grammar import OMeta

blog_grammar = """

crlf ::= '\r' '\n' => "<br />"

doublecrlf ::= <crlf> <crlf> => "</p><p>"

not_crlf ::= ~<crlf> <anything>

double_star ::= '*' '*'

bold ::= <double_star> (~<double_star> <nested_decos>)+:b <double_star>
    => "<b>%s</b>" % "".join(b)

italics ::= '*' (~'*' <nested_decos>)+:i '*' => "<i>%s</i>" % "".join(i)

underline ::= '_' (~'_' <nested_decos>)+:u '_' => "<u>%s</u>" % "".join(u)

crlfs ::= <doublecrlf> | <crlf>

decorations ::= <bold> | <italics> | <underline>

nested_decos ::= <decorations> | <not_crlf>

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
