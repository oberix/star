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
import re
import codecs
import string
import logging

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

from share import Config
from share import Bag
from longtable import LongTable

__all__ = ['sre', 'SreTemplate']
_logger = None

class SreTemplate(string.Template):
    ''' A custom template class to match the SRE placeholders.
    We need a different delimiter:
        - default is '$'
        - changhed in '\SRE'
    And a different pattern (used to match the placeholder name)
        - default is '[_a-z][_a-z0-9]*'
        - changed in '[_a-z][_a-z0-9.]*' to allow also '.' inside the
          placeholder's name (in case we need to acces just one attribute)

    NOTE: This are class attribute in the superclass, changing them at runtime
    produces no effects. The only way is subclassing. 
    Thanks to Doug Hellmann <http://www.doughellmann.com/PyMOTW/string/>.

    '''
    delimiter = '\SRE'
    idpattern = '[_a-z][_a-z0-9.]*'

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
    return config.options    

def _load_template(path):
    ''' Read template from file and generate a SreTemplate object.
    @ param path: path to the template file
    @ return: SreTemplare instance

    '''
    fd = 0
    _logger.info("Loading template.")
    try:
        fd = codecs.open(path, mode='r', encoding='utf-8')
        templ = fd.read()
        templ = re.sub("\\\\newcommand\{\\\\\\SRE\}\{.*?\}", "", templ)
        templ = SreTemplate(templ)
    except IOError, err:
        _logger.error("%s", err)
        return False
    finally:
        if fd > 0:
            fd.close()
    return templ

def _load_bags(path, template, **kwargs):
    ''' Load bag files and generates TeX code from them.

    @ param path: directory where .pickle files lives.
    @ param template: a SreTemplate instance to extract placeholders from.
    @ return: dictionary of output TeX code; the dictionary is indexed by
            bag.COD

    '''
    ret = dict()

    # Make a placeholders list to fetch only needed files and to let access to
    # single Pickle attributes.
    ph_list = [ph[2] for ph in template.pattern.findall(template.template)]

    _logger.info("Reading pickles.")
    bags = dict() # Pickle file's cache (never load twice the same file!)
    for ph in ph_list:
        ph_parts = ph.split('.')
        base = ph_parts[0]
        if not bags.get(base, False):
            # Load and add to cache
            try:
                bags[base] = Bag.load(os.path.join(path, '.'.join([base, 'pickle'])))
            except IOError, err:
                _logger.warning('%s; skipping...', err)
                continue
        if len(ph_parts) > 1: # extract attribute
            ret[ph] = eval('.'.join(['bags[base]'] + ph_parts[1:]))
        else: # just use DF/LM 
            if bags[base].TIP == 'tab':
                ret[ph] = LongTable(bags[base], **kwargs).to_latex()
            else: # TODO: handle other types
                _logger.debug('bags = %s', bags)
                _logger.warning("Unhandled bag TIP '%s' found in %s, skipping...", bags[base].TIP, base)
                continue
    return ret

def _report(dest_path, templ_path, template, bags, **kwargs):
    ''' Load report template and make the placeholders substitutions.

    @ param dest_path: path where to store output.
    @ param templ_path: template file path.
    @ param template: SreTemplate instance
    @ param bag: dictionary of LaTeX code snippetts to substitute to the
            placeholders; ths dictionary is indexed by placeholder's name.
    @ return texi2pdf exit value or -1 if an error happend.

    '''
    if not os.path.exists(os.path.dirname(dest_path)):
        os.makedirs(os.path.dirname(dest_path))
    # substitute placeholders
    # FIXME: with safe_substitute, if a placeholder is missing, no exception is
    # raised, but nothing is told to the user either.
    templ_out = template.safe_substitute(bags)
    # save final document
    template_out = templ_path.replace('.tex', '_out.tex')
    try:
        fd = codecs.open(template_out, mode='w', encoding='utf-8')
        fd.write(templ_out)
    except IOError, err:
        _logger.error("%s", err)
        return 1
    finally:
        if fd > 0:
            fd.close()
    # Call LaTeX compiler
    _logger.info("Compiling into PDF, this might take a while...")
    _logger.debug("out = %s\n\tin = %s\n\tin_path = %s",
                  os.path.join(dest_path, templ_path.replace('.tex', '')),
                  template_out, os.path.dirname(templ_path))
    ret = os.system('texi2pdf -q --batch --clean -o %s -c %s -I %s' %\
                        (os.path.join(dest_path, templ_path.replace('.tex', '')),
                         template_out, os.path.dirname(templ_path)))
    if not ret > 0:
        _logger.info("Done")
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
    src_path = os.path.abspath(src_path)
    # load config
    config = _load_config(src_path, confpath=config)

    global _logger
    _logger = logging.getLogger(os.path.basename(__file__))
    
    # Load template
    # Template is loaded first because we want to know the placeholders before
    # reading bags, so we can read just bags that will be actually used.
    try:
        templ_path = config['template']
    except KeyError:
        templ_path = os.path.join(src_path, 'main.tex')
    templ = _load_template(templ_path)
    if not templ:
        return 1

    # Load Bags
    try:
        bag_path = config['bags']
    except KeyError:
        bag_path = src_path

    _logger.debug('hlines = %s', config.get('horizontal_lines', False))
    if config.get('horizontal_lines', False) == 'True':
        kwargs.update({'hsep' : True})
    bags = _load_bags(bag_path, templ, **kwargs)
    # make report
    return _report(templ_path, templ_path, templ, bags, **kwargs)


if __name__ == "__main__":
    ''' Procedure when executing file. A directory path is needed as first
    argument.
    '''
    if len(sys.argv) < 2:
        logging.error("Specify a path containing report files")
        sys.exit(1)
    sys.exit(sre(sys.argv[1]))
