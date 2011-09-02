from pymeta.grammar import OMeta

blog_grammar = """

doublecrlf ::= '\r' '\n' '\r' '\n' => "</p><p>"

crlf ::= '\r' '\n' => "<br />"

paragraphs ::= (<doublecrlf> | <crlf> | <anything>)*:l
    => "<p>%s</p>" % "".join(l)
"""

class BlogGrammar(OMeta.makeGrammar(blog_grammar, globals())):
    pass
