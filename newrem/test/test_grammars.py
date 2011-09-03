from unittest import TestCase

from pymeta.runtime import ParseError

from newrem.grammars import BlogGrammar

class TestBlogGrammar(TestCase):

    def test_crlf(self):
        self.assertEqual(BlogGrammar("\r\n").apply("crlf")[0], "<br />")

    def test_doublecrlf(self):
        self.assertEqual(BlogGrammar("\r\n\r\n").apply("doublecrlf")[0],
            "</p><p>")

    def test_not_crlf(self):
        self.assertEqual(BlogGrammar("a").apply("not_crlf")[0], "a")

    def test_not_crlf_bare_cr(self):
        self.assertEqual(BlogGrammar("\ra").apply("not_crlf")[0], "\r")

    def test_not_crlf_fail(self):
        self.assertRaises(ParseError, BlogGrammar("\r\n").apply, "not_crlf")

    def test_bold(self):
        self.assertEqual(BlogGrammar("**asdf**").apply("bold")[0],
            "<b>asdf</b>")

    def test_bold_nested(self):
        self.assertEqual(BlogGrammar("**a*sd*f**").apply("bold")[0],
            "<b>a<i>sd</i>f</b>")

    def test_italics(self):
        self.assertEqual(BlogGrammar("*asdf*").apply("italics")[0],
            "<i>asdf</i>")

    def test_italics_nested(self):
        self.assertEqual(BlogGrammar("*a**sd**f*").apply("italics")[0],
            "<i>a<b>sd</b>f</i>")

    def test_underline(self):
        self.assertEqual(BlogGrammar("_asdf_").apply("underline")[0],
            "<u>asdf</u>")

    def test_underline_nested(self):
        self.assertEqual(BlogGrammar("_a*sd*f_").apply("underline")[0],
            "<u>a<i>sd</i>f</u>")

    def test_paragraphs_empty(self):
        self.assertEqual(BlogGrammar("").apply("paragraphs")[0], "<p></p>")

    def test_paragraphs_trivial(self):
        self.assertEqual(BlogGrammar("asdf").apply("paragraphs")[0],
            "<p>asdf</p>")

    def test_paragraphs_break(self):
        text = "asdf\r\njkl"
        self.assertEqual(BlogGrammar(text).apply("paragraphs")[0],
            "<p>asdf<br />jkl</p>")

    def test_paragraphs_multiple(self):
        text = "asdf\r\n\r\njkl"
        self.assertEqual(BlogGrammar(text).apply("paragraphs")[0],
            "<p>asdf</p><p>jkl</p>")

    def test_paragraphs_italics(self):
        text = "*asdf*"
        self.assertEqual(BlogGrammar(text).apply("paragraphs")[0],
            "<p><i>asdf</i></p>")

    def test_paragraphs_italics_cross(self):
        text = "*as\r\n\r\ndf*"
        self.assertEqual(BlogGrammar(text).apply("paragraphs")[0],
            "<p>*as</p><p>df*</p>")

class TestBlogGrammarSafety(TestCase):
    """
    BlogGrammar should be relatively impenetrable in safe mode.
    """

    def test_basic_html_escapes(self):
        text = "<br />"
        self.assertEqual(BlogGrammar(text).apply("safe_paragraphs")[0],
            "<p>&lt;br /&gt;</p>")
