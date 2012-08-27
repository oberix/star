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

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

from share.config import Config

def _get_config(confpath=None):
    if confpath is None:
        config = Config(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    else:
        config = Config(confpath)
    config.parse()
    return config.options

def _get_starks(path):
    # TODO: implement
    pass

def _save(pickeables, dest_path):
    for elem in pickleable:
        elem.save(os.path.join(dest_path, elem.name))
    
def sda(func, src_path, dest_path, confpath=None):
    config = _get_config(confpath=confpath)
    starks = _get_starks(src_path)
    transports = func(config, starks)
    _save(transports, dest_path())


if __name__ == "__main__":
    
    def test(config, starks):
        print("hallo")

    sda(test, 
        os.path.dirname(__file__), 
        os.path.dirname(__file__), 
        confpath=os.path.join(os.path.dirname(__file__), 'report_iva.cfg'))

