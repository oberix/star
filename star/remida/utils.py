# -*- coding: utf-8 -*-
import re

DUMMY_ESCAPE = [
    # (re.compile("\\"), "\\\\"), 
]

TEX_ESCAPE = [
    (re.compile(u"€"), r"\\euro"),
    (re.compile(u"%"), r"\\%"),
    (re.compile(u"&"), r"\\&"),
    (re.compile(u"\$(?!\w+)"), r"\\$"),
    (re.compile(u">=(?!\{)"), r"$\\ge$"),
    (re.compile(u"<=(?!\{)"), r"$\\le$"),
    (re.compile(u">(?!\{)"), r"$>$"),
    (re.compile(u"<(?!\{)"), r"$<$"),
    (re.compile(u"\n"), r"\\\\"),
    (re.compile(u"_"), r"\_"),
    (re.compile(u"/"), r"/\-"),
    (re.compile(u"\^"), r"\\textasciicircum"),
    (re.compile(u"~"), r"\\normaltilde"),
]

HTML_ESCAPE = [
    (re.compile(u"<"), "&lt;"),
    (re.compile(u">"), "&gt;"),
    (re.compile(u"&"), "&amp;"),
    (re.compile(u"\""), "&quot;"),
    (re.compile(u"'"), "&apos;"),
    (re.compile(u"€"), "&euro;"),
]

def unique_list(list_):
    """ Remove all duplicate elements from a list inplace, keeping the order
    (unlike set()).

    @ param: list
    """
    unique = set(list_)
    for elem in unique:
        enum = list_.count(elem)
        i = 0
        while i < (enum - 1):
            list_.remove(elem)
            i += 1

def escape(string, patterns=None):
    ''' Escape string to work with LaTeX.
    The function calls TEX_ESCAPE dictionary to metch regexp with their escaped
    version.

    @ param string: the string to escape
    @ param patterns: a pattern/string mapping dictionary
    @ return: escaped version of string

    '''
    if patterns is None:
        patterns = DUMMY_ESCAPE
    for pattern, sub in patterns:
        string = pattern.sub(sub, string)
    return string
