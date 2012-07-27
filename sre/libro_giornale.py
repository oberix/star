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

BASEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        os.path.pardir))
sys.path.append(BASEPATH)

from share.config import Config
from longtable import LongTable
import codecs

import share.generic_pickler as pickler

def generate(transport, template, outpath):
    """ Handle the production of a generate report starting from an
    appropriate Transport object.

    @ param transport: a list of Transport objects, sorted in printing order.
    @ param outpath: where to save output PDF document.
    """

    tex_dir = os.path.abspath(os.path.dirname(template))

    size = len(transport)
    for index in xrange(size):
        table = LongTable(transport[index])
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

    config = Config(os.path.join(BASEPATH, 'sre/libro_giornale/config.cfg'))
    config.parse()

    # Prepare a list of Transport objects.
    transport = []
    for pkl in config.options.get('pickle_path').split(','):
        transport.append(pickler.load(pkl))

    generate(transport, config.options.get('template'),
             config.options.get('out_path'))

    sys.exit(0)
