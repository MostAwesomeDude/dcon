from datetime import datetime
import string
import re

from PyRSS2Gen import Guid, RSS2, RSSItem

from unidecode import unidecode

alphanum = string.digits + string.lowercase
punctuation = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def abbreviate(s):
    """
    Abbreviate a string to provide a board name.

    There is no guarantee that the abbreviation will be unique.

    This function is hardcoded to provide strings of length five or less.
    """

    letters = []
    for word in s.split():
        l = word.strip()[:1].lower()
        if l in alphanum:
            letters.append(l)

    return "".join(letters)

def slugify(s):
    """
    Turn a Unicode string into a URL-safe ASCII slug.
    """

    # ASCIIfy slug. Based on http://flask.pocoo.org/snippets/5/.
    l = []
    for word in punctuation.split(s):
        l.extend(unidecode(word).split())
    return "-".join(word.strip().lower() for word in l)

def split_camel_case(s):
    """
    Split a camel-cased string into its separate parts.

    This function is currently open-coded; improvements welcome.
    """

    markers = []

    # Find each of the slicing spots.
    for i, c in enumerate(s):
        if c in string.uppercase:
            markers.append(i)

    # Huh, that's strange. It appears that there is not a single uppercase
    # letter in this string. Let's just return early.
    if not markers:
        return [s]

    # The beginning of the string might be uppercase as well; if it is, then
    # ignore the first marker. We'll still make that same cut.
    if markers[0] == 0:
        markers = markers[1:]

    pieces = []
    beginning = 0

    # Do the slices.
    for marker in markers:
        pieces.append(s[beginning:marker])
        beginning = marker

    # And the final piece.
    pieces.append(s[beginning:])

    return pieces

def make_rss2(url, title, stuff):
    """
    Make an RSS2 feed from stuff.

    Practically, the stuff is nearly always comics, but it could be anything
    else meeting the polymorphic requirements.

    `url` is a URL. `header` is a title for the feed.  `stuff` is a dictionary
    of URLs to objects with `title` and `time` attributes.
    """

    items = []
    for url, obj in stuff:
        item = RSSItem(title=obj.title, link=url, description=obj.title,
            guid=Guid(url), pubDate=obj.time)
        items.append(item)

    rss2 = RSS2(title="RSS", link=url, description=title,
        lastBuildDate=datetime.utcnow(), items=items)
    return rss2.to_xml(encoding="utf8")
