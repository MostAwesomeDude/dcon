from unittest import TestCase

from newrem.files import extend_url


class TestExtendURL(TestCase):

    def test_extend_url_example(self):
        url = "http://example.com/"
        segments = ["test", "path"]
        expected = "http://example.com/test/path"
        self.assertEqual(extend_url(url, segments), expected)
