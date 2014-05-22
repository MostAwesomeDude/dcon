# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
from parsley import makeGrammar

blog_grammar = """
crlf = '\r' '\n' -> "<br />"
doublecrlf = crlf crlf -> "</p><p>"
not_crlf = ~crlf anything
crlfs = doublecrlf | crlf

single_star = '*' ~'*'
double_star = '*' '*'

bold = double_star (~double_star nested_decos)+:b double_star
    -> "<b>%s</b>" % "".join(b)

italics = single_star (~single_star nested_decos)+:i single_star
    -> "<i>%s</i>" % "".join(i)

underline = '_' (~'_' nested_decos)+:u '_' -> "<u>%s</u>" % "".join(u)

greentext = crlfs:head '>' nested_decos+:body crlfs:tail
         -> '%s<span class="quote">&gt;%s</span>%s' % (head, "".join(body), tail)

decorations = bold | italics | underline

nested_decos = decorations | not_crlf

entities = greentext | crlfs | decorations

paragraphs = (entities | anything)*:l -> "<p>%s</p>" % "".join(l)
"""

html_grammar = """
less_than = '<' -> "&lt;"

greater_than = '>' -> "&gt;"

ampersand = '&' -> "&amp;"

apostrophe = '\\'' -> "&apos;"

quote = '"' -> "&quot;"

safe_entities = less_than | greater_than | ampersand | apostrophe | quote

safe_paragraphs = (safe_entities | entities | anything)*:l
               -> "<p>%s</p>" % "".join(l)
"""

BlogGrammar = makeGrammar(blog_grammar + html_grammar, {})
