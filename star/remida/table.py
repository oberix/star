# -*- coding: utf-8 -*-

from copy import copy
import re
from StringIO import StringIO
from star.remida import utils

__all__ = ['TexTable', 'HTMLTable']

OPEN_TEX_TAB = {'tab': """\\begin{tabu} spread \\linewidth""",
                'ltab': """\\begin{longtabu} spread \\linewidth"""}
CLOSE_TEX_TAB = {'tab':"""\\end{tabu}""",
                 'ltab':"""\\end{longtabu}"""}

# FORMATS = {
#     '@n' : u'',
#     '@g' : "\\rowfont{\\bfseries}\n",
#     '@b' : "\\\ \\tabucline- \n",
#     '@l' : "\\tabucline- \n",
#     '@i' : "\\rowfont{\\itshape} \n",
#     '@bi' : "\\rowfont{\\bfseries \\itshape} \n",
#     '@p' : "\\pagebreak \n",
# }

class Table(object):

    def __init__(self, bag):
        ''' Render data in a tabular form '''
        # pylint: disable=W0212
        self._data = bag._df
        self._table = bag._md['table']
        self._vars = bag._md['table']['vars']

        # Make a list of keys (table columns) sorting by user defined
        # order; from now on columns'es order is determined only by
        # this list, so be carefull not to mess it up.
        self._keys = self._vars.items()
        self._keys.sort(key=lambda x: x[1]['order'])
        self._keys = [k[0] for k in self._keys]

        self._headers = self._get_headers()

    def _get_headers(self):
        ''' Make a list in which every element is another list
        containing the strings that constitute a row of header.
        '''
        headers = []
        num_rows = 0
        for var in self._vars.itervalues():
            num_rows = max(num_rows, len(var['headers']))
        for row in range(num_rows):
            headers.append([])
            for key in self._keys:
                try:
                    headers[row].append(self._vars[key]['headers'][row])
                except IndexError:
                    headers[row].append(u'')
        return headers
                                              
    def _format_elem(self, idx, elem):
        form_exp = self._vars[self._keys[idx]]['float_format']
        try:
            return form_exp.format(elem)
        except ValueError:
            return unicode(elem)
    
    def _body(self, row_sep='''\n''', col_sep='''\t'''):
        try:
            self._data.sort(columns='_OR_', inplace=True)
        except KeyError:
            # leave it unsorted
            pass
        records = self._data.to_records(index=False)
        return row_sep.join(
            [col_sep.join(
                [self._format_elem(idx, elem) for idx, elem in enumerate(record)]
            ) for record in records]) + row_sep

    def body(self):
        ''' Rendere the table body '''
        return self._body()

    def header(self):
        ''' Render the table header '''
        # TODO: this might return a text only header
        return u''

    def footer(self):
        ''' Render the table footer '''
        # TODO: this might return a text only footer
        return u''
        
    def out(self):
        ''' Return the final table as a string generated following the
        in bag's metadata.  
        '''
        header = u''
        footer = u''
        if not self._table['just_data']:
            # header = utils.escape(self.header())
            # footer = utils.escape(self.footer())
            header = self.header()
            footer = self.footer()
        # body = utils.escape(self.body())
        body = self.body()
        out = [
            header,
            body,
            footer,
        ]
        return u'\n'.join(out)

class TexTable(Table):
    
    # XXX: We use long tables by default, but this may cause truble
    # when nesting tables inside \minipage or \subfigures, or any
    # other kind of TeX boxing structure.
    # OPEN_TEX_TAB = {'tab': """\\begin{tabu} spread \\linewidth""",
    #                 'ltab': """\\begin{longtabu} spread \\linewidth"""}
    # CLOSE_TEX_TAB = {'tab':"""\\end{tabu}""",
    #                  'ltab':"""\\end{longtabu}"""}
    ALIGNMENT_MAP = {
        'left': 'l',
        'l': 'l',
        'right': 'r',
        'r': 'r',
        'center': 'c',
        'c': 'c',
    }
    SEPARATORS_MAP = {
        'left': ('|', ''),
        'l': ('|', ''),
        'right': ('', '|'),
        'r': ('', '|'),
        'both': ('|', '|'),
        'b': ('|', '|'),
        'none': ('', ''), 
        'n': ('', ''),
    }

    def _make_preamble(self):
        out = u""" {"""
        for idx, key in enumerate(self._keys):
            align = TexTable.ALIGNMENT_MAP.get(self._vars[key]['align'], 'l')
            sep = TexTable.SEPARATORS_MAP.get(self._vars[key]['vsep'], ('', ''))
            out += """%sX[%s]%s""" % (sep[0], align, sep[1])
        out += "} \\firsthline \n"
        return out

    def _make_header(self, header):
        out = []
        i = 0
        exp = re.compile('^@v[0-9]*$')
        while i < len(header):
            span = 1
            while ( (i + span < len(header)) and 
                    (header[i + span] == header[i]) ):
                span += 1
            sep = TexTable.SEPARATORS_MAP.get(
                self._vars[self._keys[i]]['vsep'], ('', ''))
            out.append(
                "\\multicolumn{%s}{%sc%s}{%s}" % 
                (span, sep[0], sep[1], re.sub(exp, '', header[i]))
            )
            i += span
        out = u" & ".join(out)
        out += u" \\\ \\tabucline- \n"
        return out

    def body(self):
        return self._body(row_sep=u' \\\ \n', col_sep=u' & ')

    def header(self):
        out = self._make_preamble()
        for header in self._headers:
            out += self._make_header(header)
        return out

    def footer(self):
        ''' Render the table footer '''
        return u'\\tabucline- \n'

    def out(self):
        out = u"""\\begin{longtabu} spread \\linewidth"""
        out += super(TexTable, self).out()
        out += u"""\\end{longtabu}\n"""
        return out

class HTMLTable(Table):
    pass

