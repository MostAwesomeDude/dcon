import string
import re

from unidecode import unidecode

punctuation = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

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
