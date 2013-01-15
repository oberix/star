# -*- coding: utf-8 -*-
# pylint: disable=W1401

from copy import copy
from StringIO import StringIO
import logging

from star.remida import utils

__all__ = ['TexTable', 'HTMLTable']

OPEN_TEX_TAB = {'tab': """\\begin{tabu} spread \\linewidth""",
                'ltab': """\\begin{longtabu} spread \\linewidth"""}
CLOSE_TEX_TAB = {'tab':"""\\end{tabu}""",
                 'ltab':"""\\end{longtabu}"""}

FORMATS = {
    '@n' : str(),
    '@g' : "\\rowfont{\\bfseries}\n",
    '@b' : "\\\ \\tabucline- \n",
    '@l' : "\\tabucline- \n",
    '@i' : "\\rowfont{\\itshape} \n",
    '@bi' : "\\rowfont{\\bfseries \\itshape} \n",
    '@p' : "\\pagebreak \n",
}


class Table(object):

    def __init__(self, data, **kwargs):
        """
        @ param data: Transport object
        @ param hsep: True if you want hrizontal lines after every record

        """
        self._logger = logging.getLogger(type(self).__name__)
        self._data = data
        self.parse_md(data.md['table']['vars'])

    def parse_md(self, md):
        ''' Parse Bag's MD dictionary and estract the following non-public
        attrubutes:

        _ncols: number of table columns
        _align: columns alignment, relative size and separators
        _keys: DataFrame coluns keys
        _heading: list of lists containing headings elements

        '''
        self._ncols = len(md.keys())

        # Transpose MD
        self._align = list() # alignment

        # Extract df columns names
        self._keys = md.items()
        self._keys.sort(key=lambda x : x[1]['order'])
        self._keys = [k[0] for k in self._keys]

        # Extract heading titles
        self._heading = list() # title lists
        self._last_heading = len(md[self._keys[0]]) - 3 # last heading index
        for i in xrange(self._last_heading + 1):
            self._heading.append(list())

        # Get heading metadata
        for key in iter(self._keys):
            self._align.append(md[key]['align'])
            # First two are not titles (by spec)
            if len(md[key]) > 2:
                for i in xrange(2, len(md[key])):
                    self._heading[i-2].append(md[key]['headers'])
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

    def __init__(self, data, tab_type='tab', **kwargs):
        """
        @ param data: Transport object
        @ param hsep: True if you want hrizontal lines after every record
        """
        super(TexTable, self).__init__(data, **kwargs)
        self._hsep = self._data._md['table']['hsep']
        self._type = self._data._md['table']['type']
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
               'title': utils.escape(part[1]),
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
        utils.unique_list(title_list)
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
        ret = "\\tabucline- \n"
        span = len(self._align)
        if self._data.footnote is not None:
            ret = str().join([
                    '\multicolumn{%s}{|c|}{'% span,
                    self._data.footnote,
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
        records = StringIO()
        self._data.df.to_string(
            buf=records, float_format=lambda x: '%.3f' % x, 
            columns=self._keys, header=False, index=False)
        records.seek(0)
        for record in records.readlines():
            out += u' & '.join(record.split())
            out += ' \\\ \n'
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


    def parse_md(self, md):
        '''
        md have to be dict of dicts.
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
        self._ncols = len(md.keys())

        # Extract df columns names
        self._keys = md.items()
        self._keys.sort(key=lambda x : x[1].get('ord'))
        self._keys = [k[0] for k in self._keys]

        self._headings = dict.fromkeys(md)
        for k in self._keys:
            self._headings[k] = md[k].copy()

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
        records = StringIO()
        self._data.df.to_string(
            buf=records, float_format=lambda x: '%.3f' % x,
            columns=self._keys, header=False, index=False)
        records.seek(0)
        for record in records.readlines():
            record = record.split()
            for idx, field in enumerate(record):
                heading = self._headings[seld._keys[idx]]
                out += '''<td%s>%s</td>''' % (heading.get('td_attrs', ''), field)
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
            ret = "<hr/>" + self._data.footnote
        return str().join(ret)

    def out(self):
        ''' Return a string that contains valid Html code for a table.
        '''
        out = [
            utils.escape(self._make_header(), utils.HTML_ESCAPE),
            self._make_body(),
            #self._make_footer(),
            ]
        out = unicode(str().join(out))
        return out
