import re
import urllib.parse
from datetime import date, datetime

import titlecase
from django.contrib.humanize.templatetags.humanize import naturalday, naturaltime
from django.shortcuts import resolve_url
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.utils.text import slugify
from django_htmx.jinja import django_htmx_script

from jinja2 import Environment

VOWELS = re.compile("[AEIOUYaeiouy]")
ORD_NUMBERS_RE = re.compile(r"([0-9]+(?:st|nd|rd|th))")
SENTENCE_SPLIT = re.compile(r"(\. )")


def title_exceptions(word, **kwargs):
    word_test = word.strip("(){}<>.")

    # lowercase words
    if word_test.lower() in ["a", "an", "of", "the", "is", "or"]:
        return word.lower()

    # uppercase words
    if word_test.upper() in [
        "UK",
        "FM",
        "YMCA",
        "PTA",
        "PTFA",
        "NHS",
        "CIO",
        "U3A",
        "RAF",
        "PFA",
        "ADHD",
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI",
        "VII",
        "VIII",
        "IX",
        "X",
        "XI",
        "AFC",
        "CE",
        "CIC",
    ]:
        return word.upper()

    # words with no vowels that aren't all uppercase
    if word_test.lower() in [
        "st",
        "mr",
        "mrs",
        "ms",
        "ltd",
        "dr",
        "cwm",
        "clwb",
        "drs",
    ]:
        return word_test.title()

    # words with number ordinals
    if bool(ORD_NUMBERS_RE.search(word_test.lower())):
        return word.lower()

    # words with dots/etc in the middle
    for s in [".", "'", ")"]:
        dots = word.split(s)
        if len(dots) > 1:
            # check for possesive apostrophes
            if s == "'" and dots[-1].upper() == "S":
                return s.join(
                    [
                        titlecase.titlecase(i, callback=title_exceptions)
                        for i in dots[:-1]
                    ]
                    + [dots[-1].lower()]
                )
            # check for you're and other contractions
            if word_test.upper() in ["YOU'RE", "DON'T", "HAVEN'T"]:
                return s.join(
                    [
                        titlecase.titlecase(i, callback=title_exceptions)
                        for i in dots[:-1]
                    ]
                    + [dots[-1].lower()]
                )
            return s.join(
                [titlecase.titlecase(i, callback=title_exceptions) for i in dots]
            )

    # words with no vowels in (treat as acronyms)
    if not bool(VOWELS.search(word_test)):
        return word.upper()

    return None


def to_titlecase(s, sentence=False):
    if not isinstance(s, str):
        return s

    s = s.strip()

    # if it contains any lowercase letters then return as is
    if not s.isupper() and not s.islower():
        return s

    # if it's a sentence then use capitalize
    if sentence:
        return "".join([sent.capitalize() for sent in re.split(SENTENCE_SPLIT, s)])

    # try titlecasing
    s = titlecase.titlecase(s, callback=title_exceptions)

    # Make sure first letter is capitalise
    return s[0].upper() + s[1:]


def url_for(
    endpoint, *, _anchor=None, _method=None, _scheme=None, _external=None, **values
):
    if endpoint == "static":
        return static(values["filename"])

    if not values:
        return resolve_url(endpoint)
    url = None
    k = None
    values = {k: v for k, v in values.items() if v is not None}
    potential_args = list(values.values())
    for k in range(len(potential_args) + 1):
        try:
            url = reverse(endpoint, args=potential_args[0:k])
            break
        except NoReverseMatch:
            continue
    if k:
        values = dict(list(values.items())[k:])
    if not url:
        return resolve_url(endpoint, kwargs=values)
    if values:
        url += "?" + urllib.parse.urlencode(values)
    return url


def get_flashed_messages(*args, **kwargs):
    return []


def get_now():
    return datetime.now()


def strip_whitespace(text):
    return re.sub(r"(\s)\s+", r"\1", text)


def replace_url_params(url, **kwargs):
    parsed_url = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed_url.query)
    params = {**params, **kwargs}
    return urllib.parse.urlunparse(
        parsed_url._replace(query=urllib.parse.urlencode(params, doseq=True))
    )


def parse_datetime(d, f: str = "%Y-%m-%d", output_format=None) -> date:
    """
    Parse a date from a string
    """
    if isinstance(d, datetime):
        d = d.date()
    elif isinstance(d, date):
        pass
    else:
        d = datetime.strptime(d, f).date()
    if output_format:
        return d.strftime(output_format)
    return d


def dateformat_filter(d, f="%Y-%m-%d", o=None):
    return parse_datetime(d, f, o)


def environment(**options):
    env = Environment(**options)

    env.globals.update(
        {
            "url_for": url_for,
            "get_flashed_messages": get_flashed_messages,
            "now": get_now(),
            "django_htmx_script": django_htmx_script,
            "default_title": "UK Grantmaking Data",
            "author": "360Giving",
            "author_email": "labs@threesixtygiving.org",
            "author_website": "https://threesixtygiving.org/",
        }
    )
    env.filters.update(
        {
            "strip_whitespace": strip_whitespace,
            "dateformat": dateformat_filter,
            "replace_url_params": replace_url_params,
            "slugify": slugify,
            "to_titlecase": to_titlecase,
            "naturaltime": naturaltime,
            "naturalday": naturalday,
        }
    )
    return env
