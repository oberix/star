# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from copy import copy
import logging
import re

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "1.0"
__all__ = ['TexTable', 'unique_list', 'escape']

OPEN_TEX_TAB = {'tab': """\\begin{tabu} spread \\linewidth""",
                'ltab': """\\begin{longtabu} spread \\linewidth"""}
CLOSE_TEX_TAB = {'tab':"""\\end{tabu}""",
                 'ltab':"""\\end{longtabu}"""}


# pylint: disable=W1401

FORMATS = {
    '@n' : str(),
    '@g' : "\\rowfont{\\bfseries}\n",
    '@b' : "\\\ \\tabucline- \n",
    '@l' : "\\tabucline- \n",
    '@i' : "\\rowfont{\\itshape} \n",
    '@bi' : "\\rowfont{\\bfseries \\itshape} \n",
    '@p' : "\\pagebreak \n",
}

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

# TODO: fill this up
HTML_ESCAPE = [
    (re.compile("€"), "EURO"),
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

# TODO: move this to template.py
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
        string = re.sub(pattern, sub, string)
    return string

class Table(object):

    def __init__(self, data, **kwargs):
        """
        @ param data: Transport object
        @ param hsep: True if you want hrizontal lines after every record

        """
        self._logger = logging.getLogger(type(self).__name__)
        self._data = data
        self.parse_lm(data.lm)

    def parse_lm(self, lm):
        ''' Parse Bag's LM dictionary and estract the following non-public
        attrubutes:

        _ncols: number of table columns
        _align: columns alignment, relative size and separators
        _keys: DataFrame coluns keys
        _heading: list of lists containing headings elements

        '''
        self._ncols = len(lm.keys())

        # Transpose LM
        self._align = list() # alignment

        # Extract df columns names
        self._keys = lm.items()
        self._keys.sort(key=lambda x : x[1][0])
        self._keys = [k[0] for k in self._keys]

        # Extract heading titles
        self._heading = list() # title lists
        self._last_heading = len(lm[self._keys[0]]) - 3 # last heading index
        for i in xrange(self._last_heading + 1):
            self._heading.append(list())

        # Get heading metadata
        for key in iter(self._keys):
            self._align.append(lm[key][1])
            # First two are not titles (by spec)
            if len(lm[key]) > 2:
                for i in xrange(2, len(lm[key])):
                    self._heading[i-2].append(lm[key][i])
        self._logger.debug('_ncols = %s', self._ncols)
        self._logger.debug('_align = %s', self._align)
        self._logger.debug('_keys = %s', self._keys)
        self._logger.debug('_heading = %s', self._heading)

    def out(self):
        ''' You have to extend this class and override this method in order to
        generate a different report format.

        '''
        raise NotImplementedError


class TexTable(Table):
    """ Constitute a table that can span over multiple pages """

    def __init__(self, data, tab_type='tab', hsep=False, **kwargs):
        """
        @ param data: Transport object
        @ param hsep: True if you want hrizontal lines after every record
        """
        super(TexTable, self).__init__(data, **kwargs)
        self._hsep = str()
        self._type = tab_type
        if hsep:
            self._hsep = "\\tabucline-"

    # Non Public

    def _get_col_format(self, s, span):
        ''' Evaluate column's parameters from a title string
        @ param s: the title string
        @ param span: colspan
        @ return: a dict suitable for string substitution

        '''
        # FIXME: check s is a string
        title = s.strip('|')
        part = s.partition(title)
        ret = {'sep1': part[0],
               'span': span,
               'title': escape(part[1]),
               'sep2': part[2],
               }
        if title.strip().strip('|').startswith('@v'):
            ret['title'] = str()
        # TODO: apply translation
        return ret

    def _make_header(self, level):
        ''' Create a single line of latex table header.
        The main purpose of this method is to evaluate how to group different
        columns in a single span and define the correct '\multicolumns' for a
        LaTeX longtable.

        @ param level: a list of columns labels
        @ return: str

        '''
        out = str()
        out_list = list()
        title_list = copy(level)
        unique_list(title_list)
        for title in title_list:
            # TODO: apply translation
            colspan = level.count(title)
            params = self._get_col_format(title, colspan)
            params['span'] = colspan
            out_list.append(
                "\multicolumn{%(span)s}{%(sep1)sc%(sep2)s}{%(title)s}" % \
                    params)
        out += """ & """.join(out_list)
        # end row
        out += """ \\\ \n"""
        if level is self._heading[self._last_heading]:
            # end heading
#            out += """ \\tabucline- \endhead \n"""
            out += """ \\tabucline- \n"""
        return out

    def _make_preamble(self):
        ''' Prepare preamble for TeX table.
        Preamble is the outermost, general table structure, which will contain
        the multicolumn headers.

        @ return: str

        '''
        # table preamble
        out = OPEN_TEX_TAB[self._type] + """ {"""
        for col in self._align:
            col_format = self._get_col_format(col, 1)
            out += """%(sep1)sX[%(title)s]%(sep2)s""" % col_format
        out += """} \\firsthline\n"""
        return out

    def _make_footer(self):
        ''' Prepare footer for TeX table
        This is pretty simple: just draw a line at the bottom of the table.

        @ return: str

        '''
        ret = "\\tabucline- \\endfoot \n"
        span = len(self._align)
        if self._data.FOOTNOTE is not None:
            ret = str().join([
                    '\multicolumn{%s}{|c|}{'% span,
                    self._data.FOOTNOTE,
                    '} \\\ \\tabucline- \\endfoot \n'])
        return ret

    def _make_body(self):
        ''' Prepare data for TeX table

        @ return: str

        '''
        out = str()
        try:
            self._data.df = self._data.df.sort(columns='_OR_')
        except KeyError:
            # keep it unsorted
            pass
        try:
            self._keys.append('_FR_')
            records = self._data.df[self._keys].to_records()
            # End is used to remove _FR_ values when generating the output
            # string.
            end = -1
        except KeyError:
            self._keys.remove('_FR_')
            records = self._data.df[self._keys].to_records()
            end = None
        for record in records:
            rowstart = unicode()
            if end is not None:
                rowstart = FORMATS.get(record[end], str())
            # Remove first element because it's the df index and eventually
            # last value if it contains _FR_ values.
            out_record = list()
            for elem in list(record)[1:end]:
                if elem is None or elem == 'None':
                    out_record.append(unicode())
                else:
                    if not isinstance(elem, unicode):
                        elem = unicode(elem, encoding='utf-8')
                    out_record.append(escape(elem))
            out += rowstart + """ & """.join(out_record) + \
                " \\\ %s \n" % self._hsep
        if self._type == 'bodytab':
            out += " \n"
        else:
            out += "\\tabucline- \n"
        return out

    # Public

    def out(self):
        """ Return a string that contains valid LaTeX code for a table.

        @ return: str

        """
        headers = unicode()
        preamble = unicode()
        footer = unicode()
        close_ = unicode()

        if not self._type == 'bodytab':
            preamble = self._make_preamble()
            for heading in self._heading:
                headers += self._make_header(heading)
            footer = self._make_footer()
            close_ = CLOSE_TEX_TAB[self._type]

        out = [
            preamble,
            headers,
            self._make_body(),
            footer,
            close_
            ]
        out = unicode().join(out)
#        return unicode(out, 'utf-8')
        return out


class HTMLTable(Table):

    '''
    for tests
    python sre.py esempio_html --log-level=debug
    '''

    def __init__(self, data, hsep=False, **kwargs):
        self._logger = logging.getLogger(type(self).__name__)
        super(HTMLTable, self).__init__(data, **kwargs)


    def parse_lm(self, lm):
        '''
        lm have to be dict of dicts.
        keys are columns.
        values are dict of form:
        {
        'type':'unused',
        'ord': <int>,
        'des': <string> the th content,
        ### optional
        'th_attrs': <string> putted in `class' attr of unique tr element in thead,
        'td_attrs': <string> putted in `class' attr of unique tr element in tr in tbody,
        }
        '''
        self._ncols = len(lm.keys())

        # Extract df columns names
        self._keys = lm.items()
        self._keys.sort(key=lambda x : x[1].get('ord'))
        self._keys = [k[0] for k in self._keys]

        self._headings = dict.fromkeys(lm)
        for k in self._keys:
            self._headings[k] = lm[k].copy()

    def _make_header(self):
        '''
        sezione che costruisce l'header della tabella: thead
        '''

        out = '''<thead>'''
        out += '''<tr>'''
        for k in self._keys:
            out += '''<th%s>%s</th>''' % (
                self._headings[k].get('th_attrs', ''),
                self._headings[k]['des'].replace("|",""))
        out += '''</tr>'''
        out += '''</thead>\n'''
        return out

    def _make_body(self):
        '''
        sezione che costruisce il body della tabella: tbody
        '''

        out = '''<tbody>\n'''
        records = self._data.df[self._keys].to_records()
        #self._logger.info("In Make Body %s", records)
        for line in list(records):
            out += '''<tr>\n'''
            for idx, i in enumerate(list(line)[1:]):
                heading = self._headings[self._keys[idx]]
                out += '''<td%s>%s</td>''' % (heading.get('td_attrs', ''), i)
            out += '''\n</tr>\n'''
        out += '''</tbody>\n'''
        return out

    def _make_footer(self):
        ''' Prepare footer for Html table
        This is pretty simple: just draw a line at the bottom of the table.
        '''

        ret = str()
        span = self._align
        if self._data.footnore is not None:
            ret = "<hr/>" + self._data.footnore
        return str().join(ret)

    def out(self):
        ''' Return a string that contains valid Html code for a table.
        '''
        out = [
            escape(self._make_header(), HTML_ESCAPE),
            self._make_body(),
            #self._make_footer(),
            ]
        out = unicode(str().join(out))
        return out