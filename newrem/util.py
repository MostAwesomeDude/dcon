from datetime import datetime
from hashlib import md5
from mimetypes import guess_extension
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

def chan_filename(f):
    """
    Given an uploaded file, determine a filename for it.

    The filenames produced by this function are always reasonable and secure.
    """

    hash = md5(f.stream.read())
    f.stream.seek(0)

    md5sum = hash.hexdigest()

    extension = guess_extension(f.content_type)

    return "%s%s" % (md5sum, extension)

def slugify(s):
    """
    Turn a Unicode string into a URL-safe ASCII slug.
    """

    # ASCIIfy slug. Based on http://flask.pocoo.org/snippets/5/.
    l = []
    for word in punctuation.split(s):
        l.extend(unidecode(word).split())
    return u"-".join(word.strip().lower() for word in l).encode("ascii")

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

    `url` is a URL. `title` is a title for the feed.  `stuff` is a dictionary
    of URLs to objects with `title`, `time`, and `universe` attributes.
    """

    items = []
    for url, obj in stuff:
        item = RSSItem(title = ("%s: %s" % (obj.universe.title, obj.title)), 
            link=url, description=obj.comment,
            guid=Guid(url), pubDate=obj.time)
        items.append(item)

    rss2 = RSS2(title=title, link=url, description=title,
                lastBuildDate=datetime.utcnow(), items=items)
    return rss2.to_xml(encoding="utf8")
