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

from share import Config
import template

__all__ = ['sre', 'TexSreTemplate']

def _load_config(src_path, confpath=None):
    ''' Get configuration file.

    @ param src_path: project source directory
    @ param confpath: path to the configuration file
    @ return: options dictionary

    '''
    if confpath is None:
        confpath = os.path.join(src_path, 'config.cfg')
    if not os.path.isfile(confpath):
        logging.warning('No config file found in %s', confpath)
        return {}
    config = Config(confpath)
    config.parse()
    logging.debug(config)
    return config.options

def sre(src_path, config=None, **kwargs):
    ''' Main procedure to generate a report. 
    Besically the procedure is splitted into these steps:
        - load configuration file
        - load template
        - load bags
        - build the report
    
    In most cases every file needed to build the report is stored in the same
    directory (src_path); anyway, if a configuration file is present inside the
    src_path, it can be used to specicy different parameters.

    @ param src_path: project source path.
    @ param config: a configuration file (if None, the one inside src_path will
        be used).
    @ return: _report() return value

    '''
    config = _load_config(src_path, confpath=config)
    templ_path = 'main.tex'

    try:
        templ_path = config['template']
    except KeyError:
        if os.path.isfile(os.path.join(src_path, 'main.tex')):
            templ_path = os.path.join(src_path, 'main.tex')
	elif os.path.isfile(os.path.join(src_path, 'main.html')):
            templ_path = os.path.join(src_path, 'main.html')
    
    # Identify type just from filename
    if templ_path.endswith('.tex'):
        templ = template.TexSreTemplate(src_path, config=config)
    elif templ_path.endswith('.html'):
        templ = template.HTMLSreTemplate(src_path, config=config)

    # make report
    return templ.report()


if __name__ == "__main__":
    ''' Procedure when executing file. A directory path is needed as first
    argument.
    '''
    if len(sys.argv) < 2:
        logging.error("Specify a path containing report files")
        sys.exit(1)
    sys.exit(sre(sys.argv.pop(1)))
