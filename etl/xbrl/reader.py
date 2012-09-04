# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 2 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

import csv
from lxml import etree
import os

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'

# Keys of the dictionary returned by next().
# This is also the CVS file header.
ACC_ATTR = ['code', 'label', 'abstract', 'weight', 'order', 'parent_id']

# XBRL has tw different hierarchy, use the following names to refer to them
XBRL_CAL = 'cal' # Calculation
XBRL_PRE = 'pre' # Presentation
XBRL_INFO = 'info' # Company Info

class GenericReader(object):
    """ GenericReader acts as an abstract class, it's used just to define the
    basic interface any parser should implement.

    A parser act as an iterator over a generic datasource, presenting each
    record as a dictionary, where keys are specified by the parameter 'header'.
    """
    def __init__(self, path, **kwargs):
        """
        Initializing a parser means also opening the datasource for
        reading. This operation is very different between different types of
        datasources and can be implemented only by subclasses.

        Any Parser should accept at last the following parameters:
        @param path: The path to the datasource (regular file path or dir path or
                     DB URI).
        @param header: A list of strings to use as keys in output dictionaries.

        """
        self._path = path

    def __iter__(self):
        """ Defined to make class instances act as iterators. """
        return self

    def next(self):
        """ Return the next record in the datasource. Only subclasses can
        implement this.
        """
        raise NotImplementedError

class CSVReader(GenericReader):
    """ Parser for CSV files """

    def __init__(self, path, header=ACC_ATTR, dialect='excel', **kwargs):
        """ Initialize Parser
        @param path: path to CSV file
        @param header: list of keys each record will have
        @param dialect: CSV dialect

        """ 
        super(CSVReader, self).__init__(path, **kwargs)
        self.header = header
        self._dialect = dialect
        self._fd = open(self._path, 'r')
        self._iterator = csv.reader(self._fd, dialect=self._dialect)

    def next(self):
        """ Yield the next record as a Dict.
        @ return: Dictionary
        @ raise: StopIteration
        """
        try:
            row = self._iterator.next()
        except StopIteration:
            # EOF reached, close file and raise to notify iter()
            self._fd.close()
            raise
        ret = {}
        for index in xrange(len(self.header)):
            ret[self.header[index]] = len(row[index]) > 0 and row[index] or None
        return ret

class XBRLTaxonomyReader(GenericReader):
    """ Parser for XBRL Taxonomy """

    def __init__(self, path, use=XBRL_PRE, verbose=False, **kwargs):
        """ Initialize Parser
        
        @param path: path to the .xsd file
        @param use: what a chart of account is used for (values can be 'info',
                    'cal' or 'pre'
        @param verbose: Ture if you whant verbose account's labels

        """
        super(XBRLTaxonomyReader, self).__init__(path, **kwargs)
        self._use = use
        self._verbose = verbose

        self._entry = etree.parse(open(self._path, 'r'))
        ns = self._cleanNS(self._entry.getroot())
        
        # The entry point is just an index telling where information are stored; 
        # so first step is to read this index.
        linkbases = self._entry.xpath('//link:linkbaseRef', namespaces=ns)
        # Now place each file path in the right place, so that they are easily
        # found when we need to read them.
        # TODO: INFO is not needes, since it's included in PRE, and can be removed
        hrefs = {XBRL_INFO: [], XBRL_PRE: [], XBRL_CAL: []}
        for lb in linkbases:
            filename = lb.attrib.get("{%s}href" % ns.get('xlink'))
            if filename.find(XBRL_INFO) >= 0:
                hrefs[XBRL_PRE].append(filename)
            elif filename.find(XBRL_PRE) >= 0:
                hrefs[XBRL_PRE].append(filename)
            elif filename.find(XBRL_CAL) >= 0:
                hrefs[XBRL_CAL].append(filename)
        
        # Load info, cal or pre files
        self._calpre = {XBRL_INFO: [], XBRL_PRE: [], XBRL_CAL: []}
        dirname = os.path.dirname(path)
        for sect, files in hrefs.iteritems():
            for filename in files:
                filepath = os.path.join(dirname, filename)
                self._calpre[sect].append(etree.parse(open(filepath, 'r')))

        # load account list
        # FIXME: this could be deduced from _calpre files
        filepath = os.path.join(dirname, 'itcc-ci-2011-01-04.xsd')
        self._accounts = etree.parse(filepath)
        
        # load labels
        # FIXME: this could be deduced from itcc-ci-2011-01-04.xsd
        filepath = os.path.join(dirname, 'itcc-ci-lab-it-2011-01-04.xml')
        self._labels = etree.parse(filepath)

        # prepare iterators
        self._iterators = []
        for tree in self._calpre[self._use]:
            ns = self._cleanNS(tree.getroot())
            self._iterators.append(tree.iter(tag='{%s}loc'%ns.get('prefix')))
                                   
    def _cleanNS(self, element):
        """ Utility finction to clean 'None' keys from a dict.
        Since etree Namespaces does not accept 'None' as a dictionary key, we
        just change it to 'prefix'.

        @param element: the XML element we want to get the namespace from
        @return: a namespace dictionary without 'None's

        """ 
        ns = element.nsmap
        ns['prefix'] = ns.pop(None)
        return ns

    def _get_base(self, acc_id, attr, prefix=None):
        """ Most of the information about accounts are stored in the main
        taxonomy xsd file; this is a generic helper function to access this file
        an get any information.

        @ param acc_id: account code
        @ param attr: attribute name look for
        @ return: attribute value or False

        """ 
        ns = self._cleanNS(self._accounts.getroot())
        element = self._accounts.xpath("//prefix:element[@id='%s']" % acc_id,
                                      namespaces=ns)

        if len(element) > 0 :
            if prefix is not None:
                attr = '{%s}%s' % (ns.get(prefix), attr)
            return element[0].attrib.get(attr)
        return False

    def _get_name(self, acc_id):
        """ Find the name attribute for a given account
        @param acc_id: account code
        @return: a str
        """
        return self._get_base(acc_id, 'name')

    def _get_period(self, acc_id):
        """ Find the period attribute for a given account
        @param acc_id: account code
        @return: a str ('instant' or 'duration')
        """
        return self._get_base(acc_id, 'periodType', prefix='xbrli')

    def _get_balance(self, acc_id):
        """ Find the balance attribute for a given account
        @param acc_id: account code
        @return: a str ('credit' or 'debit')
        """
        return self._get_base(acc_id, 'balance', prefix='xbrli')

    def _get_abstract(self, acc_id):
        """ Find the abstract attribute for a given account
        @param acc_id: account code
        @return: a bool
        """
        ret = self._get_base(acc_id, 'abstract')
        # abstract is 'true' or 'false', we need to convert it to booleans
        if ret == 'true':
            return True
        return False

    def _get_label(self, acc_id, verbose=False):
        """ Find the label attribute for a given account
        @param acc_id: account code
        @param verbose: True if you want verbose labels
        @return: a str
        """
        ns = self._cleanNS(self._labels.getroot())
        labelarc = self._labels.xpath("//prefix:labelArc[@xlink:from='%s']" % acc_id,
                                     namespaces=ns)
        if len(labelarc) == 0:
            return False
        label_id = labelarc[0].attrib.get('{%s}to' % ns.get('xlink'))
        # select label verbosity
        role = 'label'
        if verbose is True:
            role = 'verboseLabel'
        label = self._labels.xpath(
            "//prefix:label[@xlink:label='%s' and \
            @xlink:role='http://www.xbrl.org/2003/role/%s']" % (label_id, role),
            namespaces=ns)
        if len(label) > 0:
            return label[0].text.encode('utf-8')
        return False
        
    def _get_weight(self, acc_id):
        """ Find the weight attribute for a given account
        @param acc_id: account code
        @return: an int
        """
        for tree in self._calpre[XBRL_CAL]:
            ns = self._cleanNS(tree.getroot())
            element = tree.xpath(
                "//prefix:calculationArc[@xlink:to='%s']" % acc_id, namespaces=ns)
            if len(element) > 0:
                return element[0].attrib.get('weight')
        return 0
            
    def _get_order(self, acc_id):
        """ Find the order attribute for a given account
        @param acc_id: account code
        @return: an int
        """ 
        for tree in self._calpre[self._use]:
            if self._use == XBRL_CAL:
                arc = 'calculationArc'
            elif self._use == XBRL_PRE or self._use == XBRL_INFO:
                arc = 'presentationArc'
            ns = self._cleanNS(tree.getroot())
            element = tree.xpath(
                "//prefix:%s[@xlink:to='%s']" % (arc, acc_id), namespaces=ns)
            if len(element) > 0:
                return element[0].attrib.get('order')
        return 0

    def _get_parent(self, acc_id):
        """ Find the parent account code
        @param acc_id: an account code
        @return: the parent account code or None
        """
        for tree in self._calpre[self._use]:
            if self._use == XBRL_CAL:
                arc = 'calculationArc'
            elif self._use == XBRL_PRE or self._use == XBRL_INFO:
                arc = 'presentationArc'
            ns = self._cleanNS(tree.getroot())
            element = tree.xpath(
                "//prefix:%s[@xlink:to='%s']" % (arc, acc_id), namespaces=ns)
            if len(element) > 0:
                return element[0].attrib.get('{%s}from' % ns.get('xlink'))
        return None

    def next(self):
        """ Yield the next record as a Dict.

        @ return: Dictionary
        @ raise: StopIteration

        """
        loc = None # XBRL loc tag
        # In XBRL we have many files to iterate, so we just iterate over them
        # one by one. Which means that, when we reach the EOF with one iterator,
        # it's time to change iterator; only when the last itarator reaches the
        # EOF a StopIteration exception is raised.
        for it in self._iterators:
            try:
                loc = it.next()
                break
            except StopIteration:
                if self._iterators.index(it) == len(self._iterators) - 1:
                    # last iterator has reached EOF
                    raise
                continue
        ns = self._cleanNS(loc)
        acc_id = loc.attrib.get('{%s}label' % ns.get('xlink'))
        ret = {
            'code': self._get_name(acc_id),
            'label': self._get_label(acc_id, verbose=self._verbose),
            'abstract': self._get_abstract(acc_id),
            'weight': self._get_weight(acc_id),
            'order': self._get_order(acc_id),
            'balance': self._get_balance(acc_id),
            'period': self._get_period(acc_id),
            'parent_id': self._get_name(self._get_parent(acc_id)),
            }
        return ret

class XBRLBalanceReader(GenericReader):
    """ Itarator over a XBRL instance """

    def __init__(self, path, **kwargs):
        # REFACTORING: This is similar to XBRLTaxonomyReader
        super(XBRLBalanceReader, self).__init__(path, **kwargs)
        self._tree = etree.parse(open(self._path, 'r'))
        self._ns = self._cleanNS(self._tree.getroot())

        acclist = []
        context_refs = self._select_context()
        for ref in context_refs:
            acclist += self._tree.xpath("./itcc-ci:*[@contextRef='%s']" % ref,
                                        namespaces=self._ns)
        self._iterator = iter(acclist)

    def _cleanNS(self, element):
        """ Utility finction to clean 'None' keys from a dict.
        Since etree Namespaces does not accept 'None' as a dictionary key, we
        just change it to 'prefix'.

        @param element: the XML element we want to get the namespace from
        @return: a namespace dictionary without 'None's

        """ 
        ns = element.nsmap
        ns['prefix'] = ns.pop(None)
        return ns

    def _select_context(self):
        """ Select a context to use in xpath as the conditional parameter 

        @ return: a list of str rappresenting context refs

        """
        out = {}
        dates = []
        it = self._tree.iter(tag='{%s}context' % self._ns.get('prefix'))
        for context in it:
            elem_date = context.xpath('.//prefix:instant', namespaces=self._ns)
            if len(elem_date) == 0:
                elem_date = context.xpath('.//prefix:endDate', namespaces=self._ns)
            date = elem_date[0].text
            dates.append(date)
            if out.get(date, False) is not False:
                out[date].append(context.attrib.get('id'))
            else:
                out[date] = [context.attrib.get('id')]
        dates.sort()
        return out[dates[-1]]

    def next(self):
        """ Return the next element from an XBRL instance file as a dictionary
        """
        row = self._iterator.next()
        ret = {
            'code': row.tag.split('}')[-1].encode('utf-8'),
            'amount': str(row.text).encode('utf-8'),
            }
        return ret
