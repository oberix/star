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

import pandas as pnd

from share.generic_pickler import GenericPickler
from account import Account
from reader import *

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'
__all__ = ['AccountChart']

class AccountChart(GenericPickler):
    """ A chart of account.

    This class contains a collection of Accounts to be used in a balance. It
    provides efficient direct, hierarchical and sequential acces to contained
    Accounts.
    """

    DEF_READER = XBRLTaxonomyReader
    CTYPES = ['ese', 'abb', 'abbsemp', 'cons']

    def __init__(self, name, ctype='ese', rootlist=[]):
        """ Assign a name and, at will, the root of an account chart; if root is
        not provided, it can be added lately using appropriate property method.
        
        @ param name: a short description of the chart
        @ param ctype: chart type, can be one of 
                ['ese' (default), 'abb', 'abbsemp', 'cons'].
        @ param rootlist: list of chart tree roots
        """
        self.name = name
        self._ctype = ctype
        self._rootlist = rootlist
        self._make_index()
        self.__to_update = True
        
    def __getitem__(self, item):
        """ delegate to dict """
        return self.__index[item]

    # Non-Public
    def _make_index(self):
        """ Create an index to access a single account directly by code """
        self.__index = {}
        for acc in self.to_list():
            self.__index[acc.code] = acc

    def _depthfirst_walk(self, account, res):
        """ Perform a depth first walk on an Account tree and saves visited
        nodes in a list.

        @ param account: account to visit
        @ res: output list
        @ return: list of Account
        
        """ 
        res.append(account)
        if account.isleaf() is False:
            account.children.sort(key=lambda x: x.order)
            for child in account.children:
                self._depthfirst_walk(child, res)
        return res

    def _create_account(self, code, label, abstract=False, weight=1, order=0,
                        period=None, balance=None, parent_id=None,
                        **kwargs):
        acc = self.__index.get(code, False)
        if acc is not False:
            # object already created: update
            acc.label = label
            acc.abstract = abstract
            acc.weight = weight
            acc.order = order
            acc.balance = balance
            acc.period = period
        else:
            # create account
            parent = None
            if parent_id is not None:
                # if parent already exist: get a reference to it, else
                # create one recursivly.
                parent = self.__index.get(parent_id, False)
                if parent is False:
                    parent = self._create_account(parent_id, '')
            acc = Account(code, label, abstract=abstract, weight=weight,
                          order=order, balance=balance, period=period,
                          parent=parent)
            self.__index[code] = acc
            # finally, if acc is a root account, put it in rootlist
            if acc.isroot():
                self.rootlist = acc
        self.__to_update = True
        return acc

    # Getters and Setters

    @property
    def rootlist(self):
        """ root getter """
        return self._rootlist

    @rootlist.setter
    def rootlist(self, account):
        """ root setter

        @ param account: acocnt to use as root
        @ raise ValueError: if account has a parent

        """
        if account.isroot() is False:
            raise ValueError("A root account must not have any parent")
        self._rootlist.append(account)

    @property
    def ctype(self):
        """ self._ctype getter """
        return self._ctype
    
    @ctype.setter
    def ctype(self, ctype):
        """ ctype setter, validate attribute values """
        if ctype not in self.CTYPES:
            raise ValueError("Type must be one of %s, '%s' received instead" %
                             (CTYPES, ctype))
        self._ctype = ctype

    @property
    def df(self):
        """ make a Dataframe out of the PdC """
        if self.__to_update is True:
            self.__df = pnd.DataFrame(self.to_dict()).transpose()
        return self.__df


    @df.setter
    def df(self, dataframe):
        """ fill a PdC from a DataFrame """
        # clean rootlist and index
        self.rootlist = []
        self.__index = {}
        index = dataframe.transpose().to_dict()
        for val in index.iteritems():
            self._create_account(val.get('code'),
                val.get('label'),
                abstract=val.get('abstract'),
                weight=val.get('weight'),
                order=val.get('order'),
                parent_id=val.get('parent_id', None))
        self.__df = dataframe
        self.__to_update = False
        
    # Public
        
    def get(self, code, *args):
        """ Get account by code.
        get(code[,default]) -> Accnount

        If an Account with code is in the AccountChart it is returned, default
        instead. If default is not given e KeyError is raised.
        
        @ param code: the code to look for
        @ return: an Account

        """
        return self.__index.get(code, *args)

    def to_list(self):
        """ Return all contained Accounts as an ordered list. The order is
        determined by a depth-first tree search, that correspond to the order
        the Accounts shuld be printed on a balance report.

        @ return: an ordered list
        """
        res = []
        for root in self.rootlist:
            self._depthfirst_walk(root, res)
        return res
    
    def to_dict(self):
        """ Return a dictionry with codes as keys and Accounts as value """
        ret = {}
        for k, v in self.__index.iteritems():
            ret[k] = {
                'code': v.code,
                'label': v.label,
                'abstract': v.abstract,
                'weight': v.weight,
                'order': v.order,
                'balance': v.balance,
                'period': v.period,
                'parent': v.parent and v.parent.code or None,
                'children': v.children and [c.code for c in v.children] or [],
                }
        return ret

    @classmethod
    def read(cls, path, reader=None, name=None, **kwargs):
        """ Read a chart of account from a datasource, different types of
        datasources can be read by passing diffferent readers; parameters
        specific to a reader can be specified as keyword arguments.        
        
        @ param path: path (or URI) to the datasource.
        @ param reader: a GenericReader instance of some kind. This objects are
                iterators that returns one dict at a time, holding values for a
                single record.
        @ param name: name to assing to the chart
        @ return: an AccountChart instance

        """
        if reader is None:
            reader = cls.DEF_READER(path, **kwargs)
        if name is None:
            name = os.path.basename(path)
        self = cls(name)
        for row in iter(reader):
            self._create_account(**row)
        return self

    def write(self, path, encoding='UTF-8', **kwargs):
        """ Write object data to datastore at path. A specific writer must be
        passed for each different datastore. If no writer is passed a default
        one will be used; the default writer is identified by the class
        attribute DEF_WRITER.
        
        To pass arguments to the writer, use **kwargs.

        @ param path: path to the datastore
        @ param writer: the writer to use (DEF_WRITER by default)

        """
        raise NotImplemented


if __name__ == '__main__':
    """ Just a test """

    chart = AccountChart('Pollo', rootlist=[])
    print type(chart)

    # test read()
    print "Testing read() ..." 
    chart = AccountChart.read('/home/mpattaro/workspace/balance/balance-2.1/taxonomies/itcc-ci/2011-01-04/itcc-ci-abb-2011-01-04.xsd', verbose=True, use='pre')
    print "Done."
