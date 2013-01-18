# -*- coding: utf-8 -*-
import re

TEX_ESCAPE = [
    (re.compile("€"), "\\officialeuro"),
    (re.compile("%"), "\\%"),
    (re.compile("&"), "\\&"),
    (re.compile("\$(?!\w+)"), "\\$"),
    (re.compile(">=(?!\{)"), r"$\\ge$"),
    (re.compile("<=(?!\{)"), r"$\\le$"),
    (re.compile(">(?!\{)"), r"$>$"),
    (re.compile("<(?!\{)"), r"$<$"),
    (re.compile("\n"), "\\\\"),
    (re.compile("_"), "\_"),
    (re.compile("/"), "/\-"),
    (re.compile("\^"), "\textasciicircum"),
    (re.compile("~"), "\normaltilde"),
    ]

HTML_ESCAPE = [
    (re.compile("<"), "&lt;"),
    (re.compile(">"), "&gt;"),
    (re.compile("&"), "&amp;"),
    (re.compile("\""), "&quot;"),
    (re.compile("'"), "&apos;"),
    (re.compile("€"), "&euro;"),
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
        patterns = TEX_ESCAPE
    for pattern, sub in patterns:
        string = pattern.sub(sub, string)
    return string
