# -*- coding: utf-8 -*-

import pandas
#import sys
#import os 
import codecs
from copy import copy

#sys.path.append(os.path.abspath(os.path.dirname(__file__)))
#import widgets
#import template

__author__ = "Marco Pattaro <marco.pattaro@servabit.it>"
__version__ = "0.1"
__all__ = ['LongTable']

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
    """ Remove all duplicate elements from a list inplace, keeping the order.
    @ param: list
    """
    unique = set(list_)
    for elem in unique:
        enum = list_.count(elem)
        for i in xrange(enum - 1):
            list_.remove(elem)

class LongTable(object):
    """ Constitute a table that chan span over multiple pages """ 

    def __init__(self, data):#, style=widget.TABLE_STYLE_DEFAULT_OPTS):
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
#        super(LongTableBox, self).__init__(self, data, **kwargs)
        self._data = data
        self._ncols = len(data.LM.keys())
        # transpose LM
        self._align = []
        self._heading1 = []
        self._heading2 = []
        self._heading3 = []
        self._keys = data.LM.items()
        self._keys.sort(key=lambda x : x[1][0])
        self._keys = [k[0] for k in self._keys]
        print self._keys
        for key in iter(self._keys):
            self._align.append(data.LM[key][1])
            self._heading1.append(data.LM[key][2])
            self._heading2.append(data.LM[key][3])
            self._heading3.append(data.LM[key][4])

            
    # Non Public (do not rely on this methods unless you really know what you
    # are doing, they are for internal use only and may suffer substantial
    # changes in the future).

    def _make_heading(self, level):
        out = str()
        out_list = list()
        title_list = copy(level)
        unique_list(title_list)
        for title in title_list:
            colspan = level.count(title)
            # factor to multiply to \linewidth to get the column width
            colfact = float(colspan) / float(len(self._align))
            if title is None or title.startswith('@'):
                # remove meta
                title = str()
            out_list.append("""\multicolumn{%s}{|@{}p{%.2f\\linewidth}@{}}{\centering %s}""" % \
                (colspan, colfact, title))
        out += """ & """.join(out_list)
        # end row
        out += """ \\vline \\\ \n """
        if level is self._heading3:
            # end heading
            out += """ \\tabucline- \endhead \n"""
        return out

    def _make_tex_header(self):
        ''' Prepare header for TeX table 

        @ return: str

        '''
        # table preamble
        out = OPEN_TEX_TAB + """ {|"""
        colspc = 1.0/len(self._align)
        for col in self._align:
            out += """X[%.2f,%s]|""" % (colspc, col)
        out += """} \\firsthline\n"""

        out += self._make_heading(self._heading1)
        out += self._make_heading(self._heading2)
        out += self._make_heading(self._heading3)

        return out

    def _make_tex_footer(self):
        ''' Prepare footer for TeX table 
        @ return: str

        '''
        raise NotImplementedError

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
            records = self._data.DF[self._keys].to_records()
            end = None
            
        for record in records:
            rowstart = str()
            if end is not None:
                rowstart = FORMATS.get(record[end], str())
            # remove first element because it's the DF index and eventually
            # last value if it contains _FR_ values
            record = map(lambda x : str(x), list(record)[1:end])
            out += rowstart + """ & """.join(record) + " \\\ \\tabucline- \n"
        return out
       
    # Public

    def to_latex(self):
        """ Return a string that constitute valid LaTeX code for a table.
        
        @ return: str

        """
        out = [
            self._make_tex_header(),
#            self._make_tex_footer(),
            self._make_tex_data(),
        ]
        out.append(CLOSE_TEX_TAB)
        out = str().join(out)
        return unicode(out, 'utf-8')


if __name__ == '__main__':
    """ Just a test """

    class Transport:
        ''' A dummy transport ''' 
        def __init__(self):
            self.DF = None
            self.LM = None

    data = Transport()
    data.LM = {
        'Paese': [0, 'l', '@v0', 'Esportatore', '@v4'],
        'X': [1, 'c', 'Esportazioni', '@v2', 'Valori'],
        'Q': [2, 'c', 'Esportazioni', '@v2', 'Quantità'],
        'PX': [3, 'c','Esportazioni', '@v2', 'Prezzi'],
        'PKD': [4, 'r', '@v1', '@v3', '\$/Kg'],
        'PKE': [5, 'r', '@v1', '@v3', '\officialeuro/Kg'],
        }
    mydict = {
        'Paese': [1,2,3,4,5,6],
        'X': [1,2,3,4,5,6],
        'Q': [1,2,3,4,5,6],
        'PX': [1,2,3,4,5,6],
        'PKD': [1,2,3,4,5,6],
        'PKE': [1,2,3,4,5,6], 
        '_OR_': [5,2,1,4,0,3],
        '_FR_': ['@bi', '@g', '@b', '@p', '@l', '@i']
        }
    data.DF = pandas.DataFrame(mydict)

    tab = LongTable(data)
    print "tab OK"
    txt = tab.to_latex()
    print "text OK"
    try:
        fd = codecs.open('/home/mpattaro/Desktop/test/pollo.tex', mode='w', encoding='utf-8')
        fd.write(txt)
    finally:
        fd.close()
    print "DONE"
    















