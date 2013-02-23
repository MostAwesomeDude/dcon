from unittest import TestCase

from ometa.runtime import ParseError

from newrem.grammars import BlogGrammar

class TestBlogGrammar(TestCase):

    def test_crlf(self):
       self.assertEqual(BlogGrammar("\r\n").crlf(), "<br />")

    def test_doublecrlf(self):
        self.assertEqual(BlogGrammar("\r\n\r\n").doublecrlf(), "</p><p>")

    def test_not_crlf(self):
        self.assertEqual(BlogGrammar("a").not_crlf(), "a")

    def test_not_crlf_fail(self):
        self.assertRaises(ParseError, BlogGrammar("\r\n").not_crlf)

    def test_bold(self):
        self.assertEqual(BlogGrammar("**asdf**").bold(), "<b>asdf</b>")

    def test_bold_nested(self):
        self.assertEqual(BlogGrammar("**a*sd*f**").bold(),
            "<b>a<i>sd</i>f</b>")

    def test_italics(self):
        self.assertEqual(BlogGrammar("*asdf*").italics(), "<i>asdf</i>")

    def test_italics_nested(self):
        self.assertEqual(BlogGrammar("*a**sd**f*").italics(),
            "<i>a<b>sd</b>f</i>")

    def test_underline(self):
        self.assertEqual(BlogGrammar("_asdf_").underline(), "<u>asdf</u>")

    def test_underline_nested(self):
        self.assertEqual(BlogGrammar("_a*sd*f_").underline(),
            "<u>a<i>sd</i>f</u>")

    def test_quote(self):
        self.assertEqual(BlogGrammar("\r\n>mfw\r\n").greentext(),
            '<br /><span class="quote">&gt;mfw</span><br />')

    def test_paragraphs_empty(self):
        self.assertEqual(BlogGrammar("").paragraphs(), "<p></p>")

    def test_paragraphs_trivial(self):
        self.assertEqual(BlogGrammar("asdf").paragraphs(), "<p>asdf</p>")

    def test_paragraphs_break(self):
        text = "asdf\r\njkl"
        self.assertEqual(BlogGrammar(text).paragraphs(),
            "<p>asdf<br />jkl</p>")

    def test_paragraphs_multiple(self):
        text = "asdf\r\n\r\njkl"
        self.assertEqual(BlogGrammar(text).paragraphs(),
            "<p>asdf</p><p>jkl</p>")

    def test_paragraphs_italics(self):
        text = "*asdf*"
        self.assertEqual(BlogGrammar(text).paragraphs(),
            "<p><i>asdf</i></p>")

    def test_paragraphs_italics_cross(self):
        text = "*as\r\n\r\ndf*"
        self.assertEqual(BlogGrammar(text).paragraphs(),
            "<p>*as</p><p>df*</p>")

class TestBlogGrammarSafety(TestCase):
    """
    BlogGrammar should be relatively impenetrable in safe mode.
    """

    def test_safe_entities_quote(self):
        text = "\""
        self.assertEqual(BlogGrammar(text).safe_entities(), "&quot;")

    def test_basic_html_escapes(self):
        text = "<br />"
        self.assertEqual(BlogGrammar(text).safe_paragraphs(),
            "<p>&lt;br /&gt;</p>")

    def test_apostrophes(self):
        text = "\'\'"
        self.assertEqual(BlogGrammar(text).safe_paragraphs(),
            "<p>&apos;&apos;</p>")

    def test_quotes(self):
        text = "\"\""
        self.assertEqual(BlogGrammar(text).safe_paragraphs(),
            "<p>&quot;&quot;</p>")

    def test_reddit_xss_sword(self):
        text = """;!--"<XSS>=&{()}"""
        sanitized = BlogGrammar(text).safe_paragraphs()
        self.assertTrue("<XSS>" not in sanitized)
