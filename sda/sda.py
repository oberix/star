#!/usr/bin/python
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
import logging

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

from share.config import load_config
from etl.stark import StarK
try:
    from Transport import Transport as Bag # Soon it will change name
except ImportError:
    from bag import Bag

__all__ = ['sda']
_logger = None

def _load_stark(path, *args):
    ''' Load data from starks files at path and return a dictionary of StarK
    objects.
    @ param path: path to the StarK's pickles
    @ param *args: list of pickle names, if empty every pickle inside path is
            read.
    @ return: dictionary of StarKs

    ''' 
    ret = dict()
    for file_ in os.listdir(path):
        if file_.endswith('.pickle'):
            if len(args) > 0 and file_.replace('.pickle', '') not in args:
                continue
            stark = StarK.load(file_)
            ret[stark.COD] = stark
    return ret

def _elaborate(module, starks, **kwargs):
    ''' Execute a callback function with datas (StarK objects) as input.
    @ param module: module to inport callback function from
    @ param starks: dictionary of input stark objects
    @ param **kwargs: dictionary of parameters to pass to the funct
    @ return: a dictionary of StarKs

    '''
    execfile(module, globals()) # TODO: are locals needed too?
    return elaborate(starks, **kwargs)
    
def _build_bags(data, lms, path):
    ''' Build Bags objects and save them to path as pickle files.
    @ param data: dictionary of input DataFrames
    @ param lms: dictionary of LM dictionaries (keys must match data's ones).
    @ param path: where the Bag's pickles will be saved
    @ return: 0 if all went good, 1 otherwhise

    ''' 
    for key in data.iterkeys():
        try:
            bag = Bag(COD=data[key].COD, TITLE=data[key].TITLE, TIP=data[key].TYPE,
                      FOOTNOTE=data[key], DF=data[key].DF, LM=lms[key])
        except KeyError:
            _logger.warning("Could not find an LM with key '%s'", key)
            continue
        bag.save(os.path.join(path, '.'.join([key, 'pickle'])))

def sda(path, config=None):
    config = load_config(path, confpath=config)

    global _logger
    logging.basicConfig(level=config.get('logLevel'))
    _logger = logging.getLogger(os.path.basename(__name__))
    
    module = config.pop('module')
    execfile(config.pop('LM'), globals())
    lms = LM

    datas = _load_stark(path, config.get('stark', []))
    out_datas = _elaborate(module, datas, **config)
    _build_bags(out_datas, lms, path)
    return 0
    
if __name__ == '__main__':
    if len(sys.argv) < 2:
        logging.error("Specify a path containing a config file")
        sys.exit(1)
    sys.exit(sda(sys.argv[1]))
