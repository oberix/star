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
import subprocess
import logging

# BASEPATH = os.path.abspath(os.path.join(
#         os.path.dirname(sys.argv[0]),
#         os.path.pardir))
# sys.path.append(BASEPATH)
# sys.path = list(set(sys.path))

import sre
from share import Config
import template

__all__ = ['sre']

_logger = None

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

def _compile_tex(file_, template, dest, fds):
    ''' Compile LaTeX, calls texi2dvi via system(3)
    
    @ param file_: main .tex file path
    @ param template: template file path, used to handle output names
    @ param dest: output file path
    @ params fds: list of temporary files'es file descriptors, we need to close
        them in order to have them removed before terminating.
    @ return: texi2dvi exit code.

    '''
    pdf_out = os.path.basename(template).replace('.tex', '.pdf')
    # create output dir if it does not exist
    if not os.path.exists(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    command = [
        "texi2dvi",
        "--pdf",
        "--batch",
        "--clean",
        "-o", os.path.join(dest, pdf_out), # output file
        "-I", os.path.dirname(template), # input path (where other files resides)
        file_, # main input file
        ]
    _logger.info("Compiling into PDF.")
    _logger.debug(" ".join(command))
    # open log file
    logfd = open(template.replace('.tex', '.log'), 'w')
    try:
        ret = subprocess.call(command, stdout=logfd, stderr=logfd)
    except IOError, err:
        _logger.error(err)
        return err.errno
    finally:
        logfd.close()
    # close temporary files (those created by TexGraph), causing deletion.
    map(lambda fd: fd.close(), fds)
    if ret > 0:
        _logger.warning(
            "texi2pdf exited with bad exit status, you can inspect what went wrong in %s", 
            os.path.join(dest, file_.replace('.tex', '.log')))
        return ret
    _logger.info("Done.")
    return ret                  

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
    global _logger
    _logger = logging.getLogger('sre')

    try:
        templ_path = config['template']
    except KeyError:
        if os.path.isfile(os.path.join(src_path, 'main.tex')):
            templ_path = os.path.join(src_path, 'main.tex')
	elif os.path.isfile(os.path.join(src_path, 'main.html')):
            templ_path = os.path.join(src_path, 'main.html')
    
    # Identify type just from filename suffix
    if templ_path.endswith('.tex'):
        templ = template.TexSreTemplate(src_path, config=config)
        report, fd_list = templ.report()
        if not isinstance(report, str):
            # Error, return errno
            return report
        return _compile_tex(report, templ_path, 
                            config.get('dest_path', os.path.dirname(templ_path)), 
                            fd_list)
    elif templ_path.endswith('.html'):
        templ = template.HTMLSreTemplate(src_path, config=config)
        report = templ.report()
        if not isinstance(report, str):
            # Error, return errno
            return report
    else:
        _logger.error("Could not find a valid template, exiting.")
        return 1
    return 0

if __name__ == "__main__":
    ''' Procedure when executing file. A directory path is needed as first
    argument.
    '''
    if len(sys.argv) < 2:
        logging.error("Specify a path containing report files")
        sys.exit(1)
    sys.exit(sre(sys.argv.pop(1)))
