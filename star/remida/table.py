# -*- coding: utf-8 -*-
# pylint: disable=W1401

from copy import copy
from StringIO import StringIO
import logging

import utils

__all__ = ['TexTable', 'HTMLTable']

OPEN_TEX_TAB = {'tab': """\\begin{tabu} spread \\linewidth""",
                'ltab': """\\begin{longtabu} spread \\linewidth"""}
CLOSE_TEX_TAB = {'tab': """\\end{tabu}""",
                 'ltab': """\\end{longtabu}"""}

FORMATS = {
    '@n': u"",
    '@g': u"\\rowfont{\\bfseries}\n",
    '@b': u"\\\ \\tabucline- \n",
    '@l': u"\\tabucline- \n",
    '@i': u"\\rowfont{\\itshape} \n",
    '@bi': u"\\rowfont{\\bfseries \\itshape} \n",
    '@p': u"\\pagebreak \n",
}

FORMATS_BT = {
    '@n': u"{0}",
    '@g': u"\\textbf{{{0}}}",
    '@b': u"{0}",
    '@l': u"{0}",
    '@i': u"\\textit{{{0}}}",
    '@bi': u"\\textbf{{\\textit{{{0}}}}}",
    '@p': u"\\pagebreak \n",
}

HTML_ALIGNMENT_MAP = {
    'left': u'textleft',
    'l': u'textleft',
    'right': u'textright',
    'r': u'textright',
    'center': u'textcenter',
    'c': u'textcenter',
}


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
        self._align = list()  # alignment

        # Extract df columns names
        self._keys = lm.items()
        self._keys.sort(key=lambda x: x[1][0])
        self._keys = [k[0] for k in self._keys]

        # Extract heading titles
        self._heading = list()  # title lists
        self._last_heading = len(lm[self._keys[0]]) - 3  # last heading index
        for i in xrange(self._last_heading + 1):
            self._heading.append(list())

        # Get heading metadata
        for key in iter(self._keys):
            self._align.append(lm[key][1])
            # First two are not titles (by spec)
            if len(lm[key]) > 2:
                for i in xrange(2, len(lm[key])):
                    self._heading[i - 2].append(lm[key][i])
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
            ret = str().join(['\multicolumn{%s}{|c|}{' % span,
                              self._data.footnote,
                              '} \\\ \\tabucline- \\endfoot \n'])
        return ret

    def _make_body(self):
        ''' Prepare data for TeX table

        @ return: str

        '''
        out = u""
        try:
            self._data._df = self._data._df.sort(columns=['_OR_'])
        except KeyError:
            # keep it unsorted
            pass

        # if fornat column _FR_ isn't present add a default format column
        if not "_FR_" in self._data._df.columns:
            self._data._df["_FR_"] = "@n"
        fr = list(self._data._df["_FR_"])

        records = self._data.df[self._keys].to_records(index=False)
        for i, record in enumerate(records):
            def to_utf8(r):
                try:
                    return unicode(str(r), 'utf8')
                except:
                    return r

            record = [to_utf8(r) for r in record]

            out += FORMATS.get(fr[i], "")
            out += u' & '.join(record)
            out += u' \\\ \n'
        return out

    def _make_bodytab(self):
        ''' Prepare data for TeX table

        @ return: str

        '''
        out = u""
        try:
            self._data._df = self._data._df.sort(columns=['_OR_'])
        except KeyError:
            # keep it unsorted
            pass

        # if fornat column _FR_ isn't present add a default format column
        if not "_FR_" in self._data._df.columns:
            self._data._df["_FR_"] = "@n"
        fr = list(self._data._df["_FR_"])
        records = self._data.df[self._keys].to_records(index=False)
        for i, record in enumerate(records):
            def to_utf8(r):
                try:
                    return unicode(str(r), 'utf8')
                except:
                    return r

            record = [FORMATS_BT.get(fr[i], "{0}").format(to_utf8(r))
                      for r in record]

            # add an empty line
            if fr[i] == "@b":
                out += u' & '.join(["" for r in record])
                out += u' \\\ \n'
            elif fr[i] == "@l":
                out += u'\\hline \n'
            out += u' & '.join(record)
            out += u' \\\ \n'
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
            body = self._make_body()
        else:
            body = self._make_bodytab()

        out = [
            preamble,
            headers,
            body,
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
        'th_attrs': <string> putted in `class' attr of unique tr element in
        thead,
        'td_attrs': <string> putted in `class' attr of unique tr element in tr
        in tbody,
        }
        '''
        self._ncols = len(lm.keys())

        # Extract df columns names
        self._keys = lm.items()
        self._keys.sort(key=lambda x: x[1].get('ord'))
        self._keys = [k[0] for k in self._keys]

        self._headings = dict.fromkeys(lm)
        for k in self._keys:
            self._headings[k] = lm[k].copy()

    def _make_header(self):
        '''
        sezione che costruisce l'header della tabella: thead
        '''
        out = u"<thead><tr>"
        for k in self._keys:
            try:
                title = unicode(self._headings[k].get('th_attrs', ''), "utf8")
            except:
                title = self._headings[k].get('th_attrs', '')
            try:
                des = unicode(self._headings[k]['des'].replace("|", ""), 
                              "utf8")
            except:
                des = self._headings[k]['des'].replace("|", "")
            out += (u"<th title='{0}'>{1}</th>"
                    "".format(utils.escape(title, utils.HTML_ESCAPE),
                              utils.escape(des, utils.HTML_ESCAPE)))
        out += u"</thead>\n"
        return out

    def _make_body(self):
        '''
        sezione che costruisce il body della tabella: tbody
        '''
        out = u"<tbody>\n"
        records = StringIO()
        self._data.df.to_string(
            buf=records, float_format=lambda x: "{0:.1f}".format(x),
            columns=self._keys, header=False, index=False, force_unicode=True)
        records.seek(0)
        for record in records.readlines():
            record = record.split()
            for idx, field in enumerate(record):
                heading = self._headings[self._keys[idx]]
                alignment_map = HTML_ALIGNMENT_MAP\
                        .get(heading.get('align', ''), '')
                field = utils.escape(field, utils.HTML_ESCAPE)
                out += (u"<td class='{0}'>{1}</td>".format(alignment_map,
                                                           field))
            out += u"\n</tr>\n"
        out += u"</tbody>\n"
        return out

    def _make_footer(self):
        ''' Prepare footer for Html table
        This is pretty simple: just draw a line at the bottom of the table.
        '''
        ret = str()
        span = self._align
        if self._data.footnore is not None:
            ret = u"<hr/>" + self._data.footnote
        return str().join(ret)

    def out(self):
        ''' Return a string that contains valid Html code for a table.
        '''
        out = [
            self._make_header(),
            self._make_body(),
            #self._make_footer(),
            ]
        out = unicode(u"".join(out))
        return out
