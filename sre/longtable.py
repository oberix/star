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

import pandas
import sys
import os 
import codecs
from copy import copy
import re

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['LongTable', 'unique_list', 'escape_latex']

OPEN_TEX_TAB = """\\begin{longtabu} to \\linewidth"""
CLOSE_TEX_TAB = """\\end{longtabu}"""

FORMATS = {
    '@n' : str(),
    '@g' : "\\rowfont{\\bfseries}\n",
    '@b' : "\\\ \\tabucline- \n",
    '@l' : "\\tabucline- \n",
    '@i' : "\\rowfont{\\itshape} \n",
    '@bi' : "\\rowfont{\\bfseries \\itshape} \n",
    '@p' : "\\pagebreak \n",
}

def unique_list(list_):
    """ Remove all duplicate elements from a list inplace, keeping the order
    (unlike set()).

    @ param: list
    """
    unique = set(list_)
    for elem in unique:
        enum = list_.count(elem)
        for i in xrange(enum - 1):
            list_.remove(elem)

def escape_latex(str_in):
    patterns = [("€", "\\officialeuro"), 
                ("%", "\\%"), 
                ("&", "\\&"),
                ("\$(?!\w+)", "\\$"),
                (">(?!\{)", "\\textgreater"),
                ("<(?!\{)", "\\textless"),
                ("\n", "\\\\"),
                ("_", "\_"),
                ("/", "/\-") # tell LaTeX that an hyphen can be inserted after a '/'
                ]
    for p, subs in patterns:
        pattern = re.compile(p)
        match = pattern.search(str_in)
        if match:
            str_in = ''.join([str_in[:match.start()], subs, str_in[match.end():]])
    return str_in

class LongTable(object):
    """ Constitute a table that can span over multiple pages """ 

    def __init__(self, data, vsep=True, hsep=True):
        """
        @ param data:
        @ param label:
        @ param headers:
        @ param caption:
        @ param footnotes:
        @ param notes_1:
        @ param notes_2:
        @ param style:

        """
        self._data = data
        self._ncols = len(data.LM.keys())
        self._vsep = str()
        self._hsep = str()
        if vsep:
            self._vsep = "|"
        if hsep:
            self._hsep = "\\tabucline-"

        # transpose LM
        self._align = []
        self._heading1 = []
        self._heading2 = []
        self._heading3 = []
        self._keys = data.LM.items()
        self._keys.sort(key=lambda x : x[1][0])
        self._keys = [k[0] for k in self._keys]
        for key in iter(self._keys):
            self._align.append(data.LM[key][1])
            self._heading1.append(data.LM[key][2])
            self._heading2.append(data.LM[key][3])
            self._heading3.append(data.LM[key][4])
            
    # Non Public 

    def _make_heading(self, level):
        """ Create a single line of latex table header.
        The main purpose of this method is to evaluate how to group different
        columns in a single span and define the correct '\multicolumns' for a
        LaTeX longtabe.

        @ param level: a list of columns labels
        @ return: str
        """
        out = str()
        out_list = list()
        title_list = copy(level)
        unique_list(title_list)
        for title in title_list:
            colspan = level.count(title)
            # factor to multiply to \linewidth to get the column width
            colfact = float(colspan) / float(len(self._align))
            if title is None or title.startswith('@v'):
                # remove meta
                title = str()
            out_list.append("""\multicolumn{%s}{%s@{}p{%.2f\\linewidth}@{}}{\centering %s }""" % \
                (colspan, self._vsep, colfact, title))
        out += """ & """.join(out_list)
        # end row
        if self._vsep:
            out += """ \\vline \\\ \n"""
        else:
            out += """ \\\ \n"""
        if level is self._heading3:
            # end heading
            out += """ \\tabucline- \endhead \n"""
        return out

    def _make_tex_header(self):
        ''' Prepare header for TeX table 

        @ return: str

        '''
        # table preamble
        out = OPEN_TEX_TAB + """ {"""
        try:
            colspc = 1.0/len(self._align)
        except ZeroDivisionError:
            # empy LM case
            colspc = 1.0
        for col in self._align:
            format = list(col)
            if len(format) < 3:
                if format[0] != '|':
                    format.insert(0, '')
                if format[-1] != '|':
                    format.append('')
            print format
            out += """%sX[%.2f,%s]%s""" % (format[0], colspc, format[1], format[2])
        out += """} \\firsthline\n"""

        out += self._make_heading(self._heading1)
        out += self._make_heading(self._heading2)
        out += self._make_heading(self._heading3)

        return out

    def _make_tex_footer(self):
        ''' Prepare footer for TeX table 
        @ return: str

        '''
        return """\\tabucline- \\endfoot \n"""

    def _make_tex_data(self):
        ''' Prepare data for TeX table 
        
        @ return: str
        
        '''
        out = str()
        try:
            self._data.DF = self._data.DF.sort(column='_OR_')
        except KeyError:
            # keep it unsorted
            pass
        try:
            self._keys.append('_FR_')
            records = self._data.DF[self._keys].to_records()
            # end is used to remove _FR_ values when generating the output
            # string
            end = -1
        except KeyError:
            self._keys.remove('_FR_')
            records = self._data.DF[self._keys].to_records()
            end = None

        for record in records:
            rowstart = str()
            if end is not None:
                rowstart = FORMATS.get(record[end], str())
            # remove first element because it's the DF index and eventually
            # last value if it contains _FR_ values
            new_record = list()
            for elem in list(record)[1:end]:
                if elem is None or elem == 'None':
                    new_record.append(str())
                else:
                    try:
                        new_record.append(escape_latex(elem.encode('utf-8')))
                    except AttributeError:
                        # element is not a string
                        new_record.append(escape_latex(str(elem).encode('utf-8')))
            record = new_record
            out += rowstart + """ & """.join(record) + " \\\ %s \n" % self._hsep
        return out
    
    # Public

    def to_latex(self):
        """ Return a string that contains valid LaTeX code for a table.
        
        @ return: str

        """
        out = [
            self._make_tex_header(),
            self._make_tex_footer(),
            self._make_tex_data(),
            ]
        out.append(CLOSE_TEX_TAB)
        out = str().join(out)
        return unicode(out, 'utf-8')


if __name__ == '__main__':
    """ Just a test """

    BASEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        os.path.pardir))
    sys.path.append(BASEPATH)
    from share.generic_pickler import GenericPickler

    class Transport(GenericPickler):
        ''' A dummy transport ''' 
        def __init__(self):
            self.DF = None
            self.LM = None

    data = Transport()
    
    data.LM = {
        "DAT_MVL": [0, 'l', '@v0', '@v1', 'Data'],
        "NAM_PAR": [2, 'l', '@v0', '@v1', 'Partner'],
        "COD_CON": [4, 'l', '@v0', '@v1', 'Codice Conto'],
        "NAM_CON": [5, 'l', '@v0', '@v1', 'Conto'],
        "DBT_MVL": [6, 'r', '@v0', '@v1', 'Dare'],
        "CRT_MVL": [7, 'r', '@v0', '@v1', 'Avere'],
        }

    data.DF = pandas.load('libro_giornale/aderit_ml.pkl')

    data.save('libro_giornale/table.pkl')

    tab = LongTable(data, vsep=False, hsep=False)
    print "tab OK"
    txt = tab.to_latex()
    print "text OK"
    try:
        fd = codecs.open('libro_giornale/table0.tex', mode='w', encoding='utf-8')
        fd.write(txt)
    finally:
        fd.close()
    print "DONE"
