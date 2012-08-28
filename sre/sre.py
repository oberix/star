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
import codecs
from string import Template
import logging

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

from share.config import Config
from sda.Transport import Transport
from longtable import LongTable

__all__ = ['sre']
_logger = None

class SreTemplate(Template):
    ''' A custom template class to match the SRE placeholders.
    '''
    delimiter = '\SRE'

def _get_config(src_path, confpath=None):
    ''' Get configuration file.

    @ param src_path: project source directory
    @ param confpath: path to the configuration file
    @ return: options dictionary
    '''
    if confpath is None:
        confpath = os.path.join(src_path, 'config.cfg')
    if not os.path.isfile(confpath):
        return {}
    config = Config(confpath)
    config.parse()
    return config.options

def _get_transports(path, dest_path=None, save_parts=False, **kwargs):
    ''' Load transport files and generates TeX code from them.

    @ param path: directory where .pickle files lives.
    @ param dest_path: directory where output files are stored (if False it's
            the same as path).
    @ param save_parts: True if you want output LaTeX code to be saved as files.
    @ return: dictionary of output TeX code; the dictionary is indexed by
            transport.COD
    '''
    ret = dict()
    _logger.info("Reading pickles, this might take a while...")

    for file_ in os.listdir(path):
        if file_.endswith('.pickle'):
            transport = Transport.load(os.path.join(path, file_))
            if transport.TIP == 'tab': # FIXME: How to choose different tables?
                ret[transport.COD] = LongTable(transport, **kwargs).to_latex()
            else:
                _logger.warning('Invalid transport TIP found in %s, skipping...', file_)
                # TODO: handle other types
                continue
            if save_parts:
                # Save generated parts in files
                file_out = os.path.join(dest_path, "%s%s.tex" % transport.COD)
                fd = codecs.open(file_out, mode='w', encoding='utf-8')
                try:
                    fd.write(file_out)
                finally:
                    fd.close()
    return ret

def _report(src_path, template, transports, dest_path=None, **kwargs):
    ''' Load report template and make the placeholders substitutions.

    @ param src_path: directory where project files lives.
    @ param template: template file path.
    @ param transport: dictionary of LaTeX code snippetts to substitute to the
            placeholers; ths dictionary is indexed by placeholder's name.
    @ param dest_path: path where to store output.
    @ return texi2pdf exit value or -1 if an error happend.
    '''
    if not os.path.exists(os.path.dirname(dest_path)):
        os.makedirs(os.path.dirname(dest_path))
    # substitute placeholders
    fd = 0
    _logger.info("Loading template.")
    try:
        fd = codecs.open(template, mode='r', encoding='utf-8')
        templ = SreTemplate(fd.read())
    except IOError, err:
        _logger.error("%s", err)
        return -1
    finally:
        if fd > 0:
            fd.close()
    templ_out = templ.substitute(transports)
    # save final document
    template_out = template.replace('.tex', '_out.tex')
    try:
        fd = codecs.open(template_out, mode='w', encoding='utf-8')
        fd.write(templ_out)
    except IOError, err:
        _logger.error("%s", err)
        return -1
    finally:
        if fd > 0:
            fd.close()
    # Call LaTeX compiler
    _logger.info("Compiling into PDF...")
    ret = os.system('texi2pdf -q --clean -o %s -c %s' %\
                  (os.path.join(dest_path, template.replace('.tex', '')), 
                   template_out))
    _logger.info("Done")
    return ret

def sre(src_path, config=None, **kwargs):
    ''' Main procedure to generate a report. 
    Besically the procedure is splitted into three steps:
        - read configuration file
        - read transports from pickles
        - build the report
    
    In most cases every file needed to build the report is stored in the same
    directory (src_path); anyway, if a configuration file is present inside the
    src_path, it can be used to specicy different parameters.

    @ param src_path: project source path.
    @ param config: a configuration file (if None, the one inside src_path will
        be used).
    @ return: _report() return value
    '''
    src_path = os.path.abspath(src_path)
    config = _get_config(src_path, confpath=config)

    global _logger
    logging.basicConfig(level = config.get('logLevel'))
    _logger = logging.getLogger(os.path.basename(__name__))

    try:
        dest_path = config['dest_path']
    except KeyError:
        dest_path = src_path
    # load tranposrts
    try:
        transport_path = config['transports']
    except KeyError:
        transport_path = src_path
    transports = _get_transports(transport_path, dest_path, **kwargs)
    # make report
    try:
        template = config['template']
    except KeyError:
        template = os.path.join(src_path, 'main.tex')
    
    return _report(src_path, template, transports, dest_path=dest_path)


if __name__ == "__main__":
    ''' Procedure when executing file. A directory path is needed as first
    argument.
    '''
    if len(sys.argv) < 2:
        logging.error("Specify a path containing report files")
        sys.exit(1)
    sys.exit(sre(sys.argv[1]))
