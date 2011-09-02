from unittest import TestCase

from newrem.grammars import BlogGrammar

class TestBlogGrammar(TestCase):

    def test_crlf(self):
        self.assertEqual(BlogGrammar("\r\n").apply("crlf")[0], "<br />")

    def test_doublecrlf(self):
        self.assertEqual(BlogGrammar("\r\n\r\n").apply("doublecrlf")[0],
            "</p><p>")

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
