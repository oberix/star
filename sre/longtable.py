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
__version__ = "1.0"
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

PATTERNS = {
    re.compile("€"): "\\officialeuro", 
    re.compile("%"): "\\%", 
    re.compile("&"): "\\&",
    re.compile("\$(?!\w+)"): "\\$",
    re.compile(">(?!\{)"): "\\textgreater",
    re.compile("<(?!\{)"): "\\textless",
    re.compile("\n"): "\\\\",
    re.compile("_"): "\_",
    re.compile("/"): "/\-", # tell LaTeX that an hyphen can be inserted after a '/'
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

def escape_latex(string, patterns=PATTERNS):
    ''' Escape string to work with LaTeX.
    The function calls PATTERNS dictionary to methc regexp with their escaped
    version.

    @ param string: the string to escape
    @ param patterns: a pattern/string mapping dictionary
    @ return: escaped version of string

    '''
    for pattern, sub in patterns.iteritems():
        string = re.sub(pattern, sub, string)
    return string

class LongTable(object):
    """ Constitute a table that can span over multiple pages """ 

    def __init__(self, data, hsep=False):
        """
        @ param data: Transport object
        @ param hsep: True if you want hrizontal lines after every record
        """
        self._data = data
        self._ncols = len(data.LM.keys())
        self._vsep = str()
        self._hsep = str()
        if hsep:
            self._hsep = "\\tabucline-"

        # Transpose LM
        self._align = list() # alignment
        
        # Extract df columns names
        self._keys = data.LM.items()
        self._keys.sort(key=lambda x : x[1][0])
        self._keys = [k[0] for k in self._keys]

        # Extract heading titles
        self._heading = list() # title lists
        self._last_heading = len(data.LM[self._keys[0]]) - 3 # last heading index
        for i in xrange(self._last_heading + 1):
            self._heading.append(list())

        # Get heading metadata
        for key in iter(self._keys):
            self._align.append(data.LM[key][1])
            # First two are not titles (by spec)
            if len(data.LM[key]) > 2:
                for i in xrange(2, len(data.LM[key])):
                    self._heading[i-2].append(data.LM[key][i])
           
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
        try:
            width = float(span) / float(len(self._align))
        except ZeroDivisionError:
            width = 1.0
        ret = {'sep1': part[0], 
               'span': span, 
               'width': width, 
               'title': escape_latex(part[1]), 
               'sep2': part[2],
               }
        if title.strip().strip('|').startswith('@v'):
            ret['title'] = str()
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
            colspan = level.count(title)
            params = self._get_col_format(title, colspan)
            params['span'] = colspan
            out_list.append(
                "\multicolumn{%(span)s}{%(sep1)sc%(sep2)s}{%(title)s}" % \
                    params)
        out += """ & """.join(out_list)
        # end row
        if self._vsep:
            out += """ \\vline"""
        out += """ \\\ \n"""
        if level is self._heading[self._last_heading]:
            # end heading
            out += """ \\tabucline- \endhead \n"""
        return out

                
    def _make_preamble(self):
        ''' Prepare preamble for TeX table.
        Preamble is the outermost, general table structure, which will contain
        the multicolumn headers.

        @ return: str

        '''
        # table preamble
        out = OPEN_TEX_TAB + """ {"""
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
        ret = str()
        span = len(self._align)
        if self._data.FOOTNOTE is not None:
            ret = self._data.FOOTNOTE 
        return str().join(['\multicolumn{%s}{|c|}{'% span, ret, '} \\\ \\tabucline- \\endfoot \n'])

    def _make_data(self):
        ''' Prepare data for TeX table 
        
        @ return: str
        
        '''
        out = str()
        try:
            self._data.DF = self._data.DF.sort(columns='_OR_')
        except KeyError:
            # keep it unsorted
            pass
        try:
            self._keys.append('_FR_')
            records = self._data.DF[self._keys].to_records()
            # End is used to remove _FR_ values when generating the output
            # string.
            end = -1
        except KeyError:
            self._keys.remove('_FR_')
            records = self._data.DF[self._keys].to_records()
            end = None
        for record in records:
            rowstart = str()
            if end is not None:
                rowstart = FORMATS.get(record[end], str())
            # Remove first element because it's the DF index and eventually
            # last value if it contains _FR_ values.
            out_record = list()
            for elem in list(record)[1:end]:
                if elem is None or elem == 'None':
                    out_record.append(str())
                else:
                    try:
                        out_record.append(escape_latex(elem.encode('utf-8')))
                    except AttributeError:
                        # element is not a string
                        out_record.append(escape_latex(str(elem).encode('utf-8')))
            out += rowstart + """ & """.join(out_record) + " \\\ %s \n" % self._hsep
        return out
    
    # Public

    def to_latex(self):
        """ Return a string that contains valid LaTeX code for a table.
        
        @ return: str

        """
        
        headers = str()
        for heading in self._heading:
            headers += self._make_header(heading)

        out = [
            self._make_preamble(),
            headers,
            self._make_footer(),
            self._make_data(),
            ]
        out.append(CLOSE_TEX_TAB)
        out = str().join(out)
        return unicode(out, 'utf-8')

