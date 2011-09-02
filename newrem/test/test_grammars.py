from unittest import TestCase

from newrem.grammars import BlogGrammar

class TestBlogGrammar(TestCase):

    def test_crlf(self):
        self.assertEqual(BlogGrammar("\r\n").apply("crlf")[0], "<br />")

    def test_doublecrlf(self):
        self.assertEqual(BlogGrammar("\r\n\r\n").apply("doublecrlf")[0],
            "</p><p>")
