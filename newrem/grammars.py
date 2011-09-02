from pymeta.grammar import OMeta

blog_grammar = """

doublecrlf ::= '\r' '\n' '\r' '\n' => "</p><p>"

crlf ::= '\r' '\n' => "<br />"
"""

class BlogGrammar(OMeta.makeGrammar(blog_grammar, globals())):
    pass
