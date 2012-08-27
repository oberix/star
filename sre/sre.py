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

import os
import sys
import codecs

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

from share.config import Config
from sda.Transport import Transport
from longtable import LongTable

def _get_config(confpath=None):
    if confpath is None:
        config = Config(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    else:
        config = Config(confpath)
    config.parse()
    return config.options

def _get_transports(path):
    ret = list()
    for file_ in os.listdir(path):
        if file_.endswith('.pickle')
        try:
            ret.append(Transport.load(os.path.join(path, file_)))
        except Exception, e:
            logging.warning("Could not load pickle %s\nInterpreter says %s", file_, e)
    return ret

def report(template, tranports, dest_path, save_parts=False):
    if not os.path.exists(os.path.dirname(dest_path)):
        os.makedirs(os.path.dirname(dest_path))
    addons = list()
    for i in xrange(len(transports)):
        if transport[i].TIP == 'tab':
            addons.append(LongTable(transports[i]).to_latex())
        else:
            # TODO: handle other types
            continue
        if save_parts:
            file_out = os.path.join(dest_path, "table%s.tex"%i)
            fd = codecs.open(file_out, mode='w', encodings='utf-8')
            try:
                fd.write(out)
            finally:
                fd.close()

    templ = load_template(template)
    templ.format(addons) # TODO: check format
    
    os.system('texi2pdf --clean -o %s -c %s' % (dest_path, template))

def sre(src_path, dest_path, config=None):
    config = _get_config(confpath=config)
    transports = _get_transports(src_path)
    report(template, transports, dest_path)
