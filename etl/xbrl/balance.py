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

from copy import copy
import pandas as pnd

from share.generic_pickler import GenericPickler
from reader import *
from writer import *

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'
__all__ = ['Balance']

COLUMNS = ['code', 'amount']

class Balance(GenericPickler):
    """ A company balance for a single year, stored inside a DataFrame (df) with the
    following columns:
        - account: the account's code
        - amount: total amount of the account, evaluated as +-(credit - debit)

    The resulting DataFrame should never duplicate an account, adding the same
    account twice results in an override; for this reason df is indexed by
    account.
    Only leaf accounts should have an amount, internal amount shold be evaluated
    later by summing childrens.

    Each instance of the class stores also the following atributes:
        - tax: tax/vat code of the company.
        - year: reference year of the balance.
        - chart: a chart of account
        - start: fiscal year start date
        - end: fiscal year end date
        - btype: balance type ('ese', 'abb', 'abbsemp', 'cons')
        
    """

    DEF_READER = XBRLBalanceReader
    DEF_WRITER = XBRLBalanceWriter

    def __init__(self, tax, year, data=[], chart=None, start=None, end=None, btype='ese'):
        """ A Balance can be initialized by passing data as a list of tuples
        (account, amount, parent); if data is None an empty balance is created,
        and new rows can be added later by calls to add_row() method.
        
        """
        self.year = year
        self.tax = tax
        self.chart = chart
        self.start = start
        self.end = end
        self.btype = btype
        
        # self.__data is a dictionary to keep real data, it gets converted to a
        # DataFrame only when self.df gets called.
        if isinstance(data, list):
            self.__data = {}
            for row in data:
                self.__data[row['code']] = row
            self.__to_update = True
        elif isinstance(data, pnd.DataFrame):
            self.df = data
        else:
            raise ValueError('parameter data must be of type list or DataFrame,\
            got %s instead' % type(data))

    def __getitem__(self, item):
        """ delegate to dict """
        return self.__data[item]

    # Non public

    def _add_row(self, row):
        """ Add rows to the balance.

        If an account is already present in self.df, the value is updated but no
        duplicates are creted.

        @ param row: tuple with a row value
        
        """
        if len(row) == len(COLUMNS):
            self.__data[row['code']] = row
        else:
            raise ValueError("Rows must be of length %s, %s received."%(len(COLUMNS),len(row)))
        self.__to_update = True

    # Getters and Setters
    @property
    def df(self):
        """ df getter

        self.__df holds the DataFrame containing data for a sigle year's
        balance.

        Since a DataFrame is easy to query, but hard (impossible) to modify in
        place, the update of this attribute is 'lazy', just when this method is
        called, however ths self.__df variable is kept as a cache, not necessary
        calculated every time. Remember to set 'self.__to_update = True'
        whenever you implement a method that should cause the self.__df update.

        """
        # If there are changes from the last call, rebuild the DataFrame
        if self.__to_update is True:
            if len(self.__data) > 0:
                data = self.__data.values()
            else:
                # prepare an empty dictionary with COLUMNS elements as keys and
                # empty lists as values
                data = dict(zip(COLUMNS, [[] for i in xrange(len(COLUMNS))]))
            self.__df = pnd.DataFrame(data, columns=COLUMNS, index=self.__data.keys())
            self.__to_update = False
        return self.__df

    @df.setter
    def df(self, df):
        """ set df and updates data

        When assigning a DataFrame to a Balance instance, we have to re-evaluate
        raw data from the DataFrame; basically this is the inverse of df.getter.

        """
        if df.columns.tolist() == COLUMNS:
            self.__data = df.transpose().to_dict()
            self.__df = pnd.DataFrame(df, columns=COLUMNS, index=self.__data.keys())
        else:
            raise ValueError('DataFrame must have the following columns: %s' % COLUMNS)
        self.__to_update = False

    # Publics

    def get(self, code, *args):
        """ Find a value by account code

        @ param code: reference year
        @ return: Balance

        """
        return self.__data.get(code, *args)

    def to_list(self):
        """ Return the balance as a list of tuples """        
        return self.__data.values()

    def to_dict(self):
        """ Return the balance as a dictionary """
        return self.__data

    @classmethod
    def read(cls, path, reader_type=None, tax=None, year=None, **kwargs):
        """ Read a balance instance from a datasource, different types of
        datasources can be read by passing diffferent readers; parameters
        specific to a reader can be specified as keyword arguments.        
        
        @ param path: path (or URI) to the datasource.
        @ param reader: a GenericReader subclass type
        @ param tax: TAX code of the company; if None the reader try to deduce
                it from the datasource.
        @ param year: balance's year; like tax, if None the reader try to read
                it from Datasource.
        @ return: a Balance instance.

        """
        if reader_type is None:
            reader_type = cls.DEF_READER
        reader = reader_type(path, **kwargs)
        obj = cls(tax, year)
        for row in iter(reader):
            obj._add_row(row)
        return obj

    def write(self, path, writer=None, **kwargs):
        """ Write object data to datastore at path. A specific writer must be
        passed for each different datastore. If no writer is passed a default
        one will be used; the default writer is identified by the class
        attribute DEF_WRITER.
        
        To pass arguments to the writer, use **kwargs.

        @ param path: path to the datastore
        @ param writer: the writer to use (DEF_WRITER by default)

        """
        if writer is None:
            writer = self.DEF_WRITER(self, **kwargs)
        writer.write(path)
        

if __name__ == '__main__':
    """ Just a test """
    from account_chart import AccountChart
    filename = '/home/mpattaro/workspace/balance/balance-2.1/test/test_ese.xbrl'
    bal = Balance.read(filename)
    chartpath = '/home/mpattaro/workspace/balance/balance-2.1/taxonomies/itcc-ci/2011-01-04/itcc-ci-abb-2011-01-04.xsd'
    bal.chart = AccountChart.read(chartpath, use='cal')
    bal.chart.ctype = 'abb'
    bal.btype = 'abb'
    bal.year = '2064'
    out = '/home/mpattaro/Desktop/pollo.xbrl'
    bal.write(out)
