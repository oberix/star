# -*- coding: utf-8 -*-
#from copy import copy
import re
#from StringIO import StringIO
from star.remida import utils
from lxml.html import builder as HTML
from lxml import html

__all__ = ['Table', 'TexTable', 'HTMLTable']

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
        ''' Render data in a tabular form 

        @ param bag: a star.Bag instance
        '''
        # pylint: disable=W0212
        self._data = bag._df # do not make unnecessary copies
        self._table = bag.md['table']
        self._vars = bag.md['table']['vars']

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
        ''' Apply a format to an element, if the element is a float,
        the md key 'float_format' will be used.
        
        @ param idx, element index
        @ param elem, the element's value
        @ return: a uicode string
        '''
        form_exp = self._vars[self._keys[idx]]['float_format']
        try:
            return form_exp.format(elem)
        except ValueError:
            return unicode(elem)
    
    def _make_header_elem(self, span, sep, elem, exp):
        ''' This is a template method to generate a single header
        cell. Table subclasses should provide a concrete
        implementation.

        @ param span: an integer to indicate the colspan of the cell
        @ param sep: a tuple with two elements containing left and
            right separators respectivly.
        @ param elem: the cell value.
        @ param exp: a compiled regular expression to match void
            cells.
        @ return: a list of language specific formatted header
            elements.
        '''
        # TODO: there could be an implementation here
        raise NotImplementedError

    def _make_header(self, header):
        ''' Buld one level of table header.
        @ param header: a list with elements of the header being built.
        @ return: a list with all the header elements formatted for
            the specific language.
        '''
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
            out.append(self._make_header_elem(span, sep, header[i], exp))
            i += span
        return out

    def _to_records(self):
        ''' Turn data in a list of lists.
        @ return: A list of lists.
        '''
        try:
            self._data.sort(columns='_OR_', inplace=True)
        except KeyError:
            # leave it unsorted
            pass
        return self._data.to_records(index=False)

    def _body(self, row_sep='''\n''', col_sep='''\t''', escape=None):
        ''' Buld the table body. 

        This is a template method to let subclasses do the dirty job,
        while still providing a simple text output. Infact, in most
        cases, changing this method's parameters is enough to obtain
        the result.

        @ param row_sep: row separators, what indicates the end of a
            row (default: '\n')
        @ param col_sep: column separators, what indicated the end of
            a column (default: '\t')
        @ return: a string
        '''
        records = self._to_records()
        ret = row_sep.join(
            [col_sep.join(
                [utils.escape(self._format_elem(idx, elem),
                              patterns=escape)
                 for idx, elem in enumerate(record)]
            ) for record in records]) + row_sep
        return ret

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
        
    def _out(self):
        header = u''
        footer = u''
        if not self._table['just_data']:
            header = self.header()
            footer = self.footer()
        body = self.body()
        out = [
            header,
            body,
            footer,
        ]
        return out

    def out(self):
        ''' Return the final table as a string generated following the
        in bag's metadata.  
        '''
        return u'\n'.join(self._out())

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
            align = TexTable.ALIGNMENT_MAP.get(
                self._vars[key]['align'], 'l')
            sep = TexTable.SEPARATORS_MAP.get(
                self._vars[key]['vsep'], ('', ''))
            out += """%sX[%s]%s""" % (sep[0], align, sep[1])
        out += "} \\firsthline \n"
        return out

    
    def _make_header_elem(self, span, sep, elem, exp):
        return "\\multicolumn{%s}{%sc%s}{%s}" % \
            (span, sep[0], sep[1], 
             exp.sub('', utils.escape(elem, patterns=utils.TEX_ESCAPE)))

    def body(self):
        return self._body(row_sep=u' \\\ \n', col_sep=u' & ',
                          escape=utils.TEX_ESCAPE)

    def header(self):
        out = self._make_preamble()
        for header in self._headers:
            out += u" & ".join(self._make_header(header))
            out += " \\\ \\tabucline- \n"
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

    ALIGNMENT_MAP = {
        'left': 'left',
        'l': 'left',
        'right': 'right',
        'r': 'right',
        'center': 'center',
        'c': 'center',
    }

    def _make_header_elem(self, span, sep, elem, exp):
        return HTML.TH(
            exp.sub('', utils.escape(elem, patterns=utils.HTML_ESCAPE)),
            colspan="%s" % span)

    def header(self):
        return HTML.THEAD(*[HTML.TR(*self._make_header(header)) 
                            for header in self._headers])

    def body(self):
        records = self._to_records()
        return HTML.TBODY(
            *[HTML.TR(
                *[HTML.TD(
                    utils.escape(self._format_elem(idx, elem)),
                    align=self.ALIGNMENT_MAP.get(
                        self._vars[self._keys[idx]]['align'], 'l')
                ) for idx, elem in enumerate(record)]
            ) for record in records])

    def footer(self):
        return HTML.TFOOT(
            HTML.TR(
                HTML.TD(
                    self._table['footer'],
                    colspan="%s" % len(self._keys),
                    align='center')))

    def out(self):
        return html.tostring(HTML.TABLE(*self._out(), border="1"),
                             pretty_print=True, encoding=unicode)
