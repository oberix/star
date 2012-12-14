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
import re
import codecs
import os
import string
import logging

# import sre
from share.bag import Bag
from table import TexTable, HTMLTable
from graph import TexGraph, HTMLGraph

__all__ = ['HTMLSreTemplate', 'TexSreTemplate']

# pylint: disable=W1401

class AbstractSreTemplate(string.Template):
    ''' Abstract Class for Sre template parsing
    '''

    comment = "#.*" # just an example with Python comments.
    _suffix = None # Template file suffix
    _suffix_out = None # Output file suffix

    def __init__(self, templ_path, config=None):
        self._src_path = os.path.dirname(os.path.abspath(templ_path))
	self._logger = logging.getLogger(type(self).__name__)
        self._fds = list() # list of opened file descriptors
	# load template
        self._templ_path = templ_path
	self._load_template(self._templ_path)
	# load Bags
	try:
            bag_path = config['bags']
	except KeyError:
            bag_path = self._src_path
	self.bags = self._load_bags(bag_path)
	# other paths
	try:
            self._dest_path = config['dest_path']
	except KeyError:
            self._dest_path = self._src_path

    def _load_template(self, path):
        ''' Read template from file and generate a TexSreTemplate object.
        @ param path: path to the template file
        @ return: AbstractSreTemplare instance

        '''
        self._logger.info("Loading template.")
        fd = codecs.open(path, mode='r', encoding='utf-8')
        try:
            templ = fd.read()
            # Remove comments
            templ = re.sub(re.compile(self.comment), str(), templ)
            super(AbstractSreTemplate, self).__init__(templ)
        except IOError, err:
            self._logger.error(err)
            sys.exit(err.errno)
        finally:
            fd.close()

    def _load_bags(self, path, **kwargs):
        ''' Load bag files and generates TeX code from them.

        @ param path: directory where .pickle files lives.
        @ param template: a TexSreTemplate instance to extract placeholders
            from.
        @ return: dictionary of output TeX code; the dictionary is indexed by
            bag.COD

        '''
        ret = dict()
        # Make a placeholders list to fetch only needed files and to let access
        # to single Pickle attributes.
        ph_list = [ph[2] for ph in self.pattern.findall(self.template)]
        try:
            ph_list.remove(str()) # Remove placeholder command definition.
        except ValueError:
            pass
        # In case of multiple instance of a placeholder, evaluate only once.
        ph_list = list(set(ph_list))
        self._logger.info("Reading pickles...")
        bags = dict() # Pickle file's cache (never load twice the same file!)
        for ph in ph_list:
            ph_parts = ph.split('.')
            base = ph_parts[0]
            if not bags.get(base, False):
                # Load and add to cache
                self._logger.debug('Now loading: %s', os.path.join(
                        path, '.'.join([base, 'pickle'])))
                try:
                    bags[base] = Bag.load(os.path.join(path, '.'.join(
                                [base, 'pickle'])))
                except IOError, err:
                    self._logger.warning('%s; skipping...', err)
                    continue
            # Generate string to substitute to the placeholder
            if bags[base].stype == 'tab':
                ret[base] = self._make_table(bags[base], **kwargs).out()
            elif bags[base].stype == 'ltab':
                ret[base] = self._make_table(bags[base], tab_type='ltab', **kwargs).out()
            elif bags[base].stype == 'bodytab':
                ret[base] = self._make_table(bags[base], tab_type='bodytab', **kwargs).out()
            elif bags[base].stype == 'graph':
                ret[base], fd = self._make_graph(bags[base], **kwargs).out()
                self._fds.append(fd)
            else: # TODO: handle other types
                self._logger.debug('bags = %s', bags)
                self._logger.warning(
                    "Unhandled bag stype '%s' found in %s, skipping...", 
                    bags[base].stype, base)
                continue
            if len(ph_parts) > 1 and \
                    hasattr(bags[base], '.'.join(ph_parts[1:])):
                # extract attribute
                # TODO: apply translation
                ret[ph] = bags[base].__getattribute__('.'.join(ph_parts[1:]))
        return ret

    def _make_table(self, data, **kwargs):
        ''' Create a table from the given DataFrame.
        This is a virtual method and must be overriden by subclass
        implementation.

        @ return: a Table object
        ''' 
        raise NotImplementedError

    def _make_graph(self, data, **kwargs):
        ''' Create a table from the given DataFrame.
        This is a virtual method and must be overriden by subclass
        implementation.
        
        @return: a Graph object
        ''' 
        raise NotImplementedError

    def report(self, **kwargs):
        ''' Load report template and make the placeholders substitutions.

        @ return texi2pdf exit value or -1 if an error happend.

        '''
        if not os.path.exists(os.path.dirname(self._dest_path)):
            os.makedirs(os.path.dirname(self._dest_path))

        # substitute placeholders
        templ_out = self.safe_substitute(self.bags, encoding='utf-8')
        # save final document
        template_out = self._templ_path.replace(self._suffix, self._suffix_out)
        fd = codecs.open(template_out, mode='w', encoding='utf-8')
        try:
            fd.write(templ_out)
        except IOError, err:
            self._logger.error(err)
            return err.errno
        finally:
            fd.close()
        return template_out, self._fds


class TexSreTemplate(AbstractSreTemplate):
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
    comment = "%.*" 
    _suffix = '.tex'
    _suffix_out = '_out.tex'

    input_re = [re.compile("\\import{.*}"), 
                re.compile("\\input{.*}")]

    def _substitute_includes(self):
        ''' Change input and includes LaTeX statements inside a template to
        refere to the _out files
        ''' 
        for regexp in TexSreTemplate.input_re:
            matches = re.findall(regexp, self.template)
            for match in matches:
                repl = match.split('}')
                repl.remove('')
                repl.append('out')
                repl = ''.join(['_'.join(repl), '}'])
                self.template = self.template.replace(match, repl)

    def _make_table(self, data, **kwargs):
        return  TexTable(data, **kwargs)

    def _make_graph(self, data, **kwargs):
        return  TexGraph(data, **kwargs)

    def report(self, **kwargs):
        self._substitute_includes()
        return super(TexSreTemplate, self).report(**kwargs)

class HTMLSreTemplate(AbstractSreTemplate):
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
    # TODO: change delimiter for HTML
    # TODO: check comment
    delimiter = '\SRE'
    idpattern = '[_a-z][_a-z0-9.]*' 
    comment = "<!--.*-->"
    _suffix = '.html'
    _suffix_out = '_out.html'

    def _make_table(self, data, **kwargs):
        return  HTMLTable(data, **kwargs)

    def _make_graph(self, data, **kwargs):
        return  HTMLGraph(data, **kwargs)

