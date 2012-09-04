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

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'

from lxml import etree
from decimal import Decimal

# Type specific namespace's attributes
TSPEC_NS = {
    'itcc-ci-abb': 'http://www.infocamere.it/itnn/fr/itcc/ci/abb/2011-01-04',
    'itcc-ci-ese': 'http://www.infocamere.it/itnn/fr/itcc/ci/ese/2011-01-04',
    'itcc-ci-abbsemp': 'http://www.infocamere.it/itnn/fr/itcc/ci/abbsemp/2011-01-04',
    'itcc-ci-cons': 'http://www.infocamere.it/itnn/fr/itcc/ci/cons/2011-01-04',
}

# Deault namespace's attributes
DEF_NS = {
    None: 'http://www.xbrl.org/2003/instance',
    'itcc-ci': 'http://www.infocamere.it/itnn/fr/itcc/ci/2011-01-04',
    'link': 'http://www.xbrl.org/2003/linkbase',
    'xlink': 'http://www.w3.org/1999/xlink',
    'iso4217':"http://www.xbrl.org/2003/iso4217",
}

class GenericWriter(object):
    """ A writer is an object capable of writing a specific type of document;
    this kind of writer expect to receive in input an object containing a pandas
    DataFrame and a standard dict, the former holding data and the second with
    eventual metadata.

    Each subclass is expected to implement a write() method.

    """

    def __init__(self, obj, **kwargs):
        """ Initialize writer saving a reference to the data object.
        
        @ param obj: the data object

        """
        self._obj = obj

    def write(self, path):
        """ Print object data to path.
        This method must be implemented in the subclasses.

        @ param path: destination path

        """
        raise NotImplementedError


class XBRLBalanceWriter(GenericWriter):
    """
    """
    
    def __init__(self, obj, prev_obj=None, namespace=DEF_NS, encoding='UTF-8',
                 entry_prefix="itcc-ci", entry_suffix="2011-01-04.xsd",
                 scenario='Depositato', **kwargs):
        """ Initialize writer
        
        @ param obj: the Balance obj with data from the current fiscal year.
        @ param prev_obj: the Balance obj with data from the previous fiscal
                year.
        @ param namespace: namespace to use in the XML document
        @ param encoding: charset encoding to use in output (default UTF-8)
        @ param entry: XBRL taxonomy entry point (the name of the file)
        @ param scenario: scenario value for XBRL document

        """ 
        # Params
        super(XBRLBalanceWriter, self).__init__(obj)
        self.encoding = encoding
        self._prev_obj = prev_obj
        self._prefix = entry_prefix
        self._entry = "%s-%s-%s" % (entry_prefix, self._obj.chart.ctype,
                                    entry_suffix)
        self._scenario = scenario
        # namespace
        key = "%s-%s" % (entry_prefix, self._obj.btype)
        namespace.update(dict([(key, TSPEC_NS[key])]))
        self._ns = namespace

        # Local data structure
        #  _contexts and _units are used to keep track of existing units and
        # contexts subtrees; _root is the XML document root. Before write()
        # _root is incapsulated in an ElementTree.
        self._contexts = {}
        self._units = {}
        self._root = None
        # start building
        self._buildtree()

    def _gen_root(self):
        """ Generate document root

        @ return: etree.Element

        """
        root = etree.Element('xbrl', nsmap=self._ns)
        etree.SubElement(root, '{%s}schemaRef' % self._ns.get('link'), 
                         attrib={'{%s}type' % self._ns.get('xlink'): "simple", 
                                 '{%s}href' % self._ns.get('xlink'): self._entry})
        return root

    def _gen_unit(self, acc):
        """ Generate a unit subtree or return an exisiting one 
        
        @ param: an Account instance
        @ return: str, the element's id
        """
        # TODO: this is a dummy implementation since it always create and
        # returns ISO EUR unit, that's fair enough for most (all) of Servabit
        # needs, but should become more general in the future.
        if self._units.get('EUR', False) is False:
            self._units['EUR'] = etree.Element(
                'unit', attrib={'id': 'EUR'}, nsmap=self._ns)

            measure = etree.SubElement(self._units['EUR'], 'measure',
                                       nsmap=self._ns)
            measure.text = 'iso4217:EUR'
            self._root.insert(1, self._units['EUR'])
        return 'EUR'

    def _gen_cid(self, balance, acc):
        """ Context id hash function: generate a distinct id for each unique context

        @ param balance: the balance intance
        @ param acc: an Account obj
        @ return: str, the element's id
        """
        return "%s_%s" % (acc.period, balance.year)
                    
    def _gen_context(self, balance, acc):
        """ Generate a context subtree or return an exisiting one 
        
        @ param balance: the balance intance
        @ param acc: an Account obj
        @ return: str, the element's id
        """
        cid = self._gen_cid(balance, acc)
        if self._contexts.get(cid, False) is False:
            self._contexts[cid] = etree.Element('context', attrib={'id':cid},
                                                nsmap=self._ns)
            # context entity
            entity = etree.SubElement(self._contexts[cid], 'entity',
                                      nsmap=self._ns)
            iden = etree.SubElement(entity, 'identifier',
                                    attrib={'scheme':"www.infocamere.it"},
                                    nsmap=self._ns)
            # FIXME: this is a default, dicover whet this means
            iden.text = "AZ17"
            
            # context period
            period = etree.SubElement(self._contexts[cid], 'period',
                                      nsmap=self._ns)
            # if start/end year are missing, assume 1-1/31-12
            if balance.start is None:
                balance.start = "%s-01-01" % balance.year
            if balance.end is None:
                balance.end = "%s-12-31" % balance.year

            if acc.period == 'duration':                
                st = etree.SubElement(period, 'startDate', nsmap=self._ns)
                st.text = balance.start
                et = etree.SubElement(period, 'endDate', nsmap=self._ns)
                et.text = balance.end
            else: # instant
                instant = etree.SubElement(period, 'instant', nsmap=self._ns)
                instant.text = balance.end

            # scenario
            scenario = etree.SubElement(self._contexts[cid], 'scenario',
                                        nsmap=self._ns)
            scen_tag = '{%s}scen' % self._ns['itcc-ci-%s' % balance.chart.ctype]
            scen = etree.SubElement(scenario, scen_tag, nsmap=self._ns)
            scen.text = self._scenario
            # finally
            self._root.insert(1, self._contexts[cid])
        return cid

    def _decimals(self, amount):
        """ Find the number of decimal scale in amount 
        
        @ parame amount: amount to evaluate
        @ return: integer
        """
        return abs(Decimal(amount).as_tuple().exponent)
        
    def _gen_rows(self, balance):
        """ Generate balance rows and relative contexts and units

        @ param balance: Balace object
        @ return: True
        @ raise KeyError: if balance does not match it's chart
        """
        accounts = balance.to_dict()
        for acc in accounts.itervalues():
            tag = '{%s}%s' % (self._ns.get(self._prefix), acc.get('code'))
            row = etree.SubElement(self._root, tag)
            row.text = acc.get('amount')
            row.attrib.update({
                    'unitRef': self._gen_unit(acc),
                    'decimals': str(self._decimals(acc.get('amount'))),
                    })
            try:
                row.attrib['contextRef'] = self._gen_context(balance, balance.chart[acc['code']])
            except KeyError:
                raise KeyError("Could not find account code '%s' in chart" % acc['code'])
        return True
        
    def _buildtree(self):
        """ Method responsible to build the XML document tree that will be
        printed by write().
        
        """
        self._root = self._gen_root()
        self._gen_rows(self._obj)
        if self._prev_obj is not None:
            self._gen_rows(self._prev_obj)
        
    def write(self, path):
        try:
            fd = open(path, 'w')
            etree.ElementTree(element=self._root).write(
                fd, encoding=self.encoding, pretty_print=True,
                xml_declaration=True)
        except:
            raise
        finally:
            fd.close()
        
class CSVWriter(GenericWriter):
    """
    """
    pass
