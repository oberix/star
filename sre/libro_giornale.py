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

import sys
import os

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)

from share.config import Config
from longtable import LongTable
import codecs

import share.generic_pickler as pickler

def generate(transport, template, outpath, vsep=True, hsep=True):
    """ Handle the production of a generate report starting from an
    appropriate Transport object.

    @ param transport: a list of Transport objects, sorted in printing order.
    @ param outpath: where to save output PDF document.
    """

    tex_dir = os.path.abspath(os.path.dirname(template))

    size = len(transport)
    for index in xrange(size):
        table = LongTable(transport[index], hsep=hsep)
        out = table.to_latex()
        
        table_out = os.path.join(tex_dir, "table%s.tex" % index)
    
        fd = codecs.open(table_out, mode='w', encoding='utf-8')
        try:
            fd.write(out)
        finally:
            fd.close()

    if not os.path.exists(os.path.dirname(outpath)):
        os.makedirs(os.path.dirname(outpath))
    os.system('texi2pdf -o %s -I %s -c %s' % (outpath, tex_dir, template))


if __name__ == '__main__':
    """ Main flow """ 

    class Transport(pickler.GenericPickler):
        """ A dummy transport.
        This is a dummy implementation of Transport class specification, just to
        have something to load/save in pickle when testing the engine.
        """
        def __init__(self):
            self.DF = None
            self.LM = None

    # Phase 1: generate transport object and save it as a pickle (the last
    # action is not crucial, but this is a test... the more the merryer!)
    import pandas
    data = Transport()
    
    # data.LM = {
    #     "DAT_MVL": [0, '|c|', '|@v0|', '|@v1|', '|Data'],
    #     "NAM_PAR": [2, 'l|', '|@v0|', '|@v1|', 'Partner'],
    #     "COD_CON": [4, 'l|', '|@v0|', '|@v1|', 'Codice Conto|'],
    #     "NAM_CON": [5, 'l|', '@v2|', '@v3|', 'Conto'],
    #     "DBT_MVL": [6, 'r|', '@v2|', '@v3|', 'Dare'],
    #     "CRT_MVL": [7, 'r|', '@v2|', '@v3|', 'Avere|'],
    #     }

    data.LM = {
        "DAT_MVL": [0, '|c|', '|@v0|', '|@v1|', '|c|', '|Data'],
        "NAM_PAR": [2, 'l|', '|@v0|', '|@v1|', '|c|', 'Partner'],
        "COD_CON": [4, 'l|', '|@v0|', '|@v1|', '|c|', 'Codice Conto|'],
        "NAM_CON": [5, 'l|', '@v2|', '@v3|', 'd|', 'Conto'],
        "DBT_MVL": [6, 'r|', '@v2|', '@v3|', 'd|', 'Dare'],
        "CRT_MVL": [7, 'r|', '@v2|', '@v3|', 'd|', 'Avere|'],
        }

    data.DF = pandas.load('libro_giornale/aderit_ml.pkl')

    data.save('libro_giornale/table.pkl')

    # Phase 2: load transports(s) from pickles, generate LaTeX and compile!
    config = Config(os.path.join(BASEPATH, 'sre/libro_giornale/config.cfg'))
    config.parse()

    # Prepare a list of Transport objects.
    transport = []
    for pkl in config.options.get('pickle_path').split(','):
        transport.append(pickler.load(pkl))

    print transport
    generate(transport, config.options.get('template'),
             config.options.get('out_path'),
             hsep=True)

    sys.exit(0)
