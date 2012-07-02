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

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'
__all__ = ['Balance']

COLUMNS = ['account', 'amount']
EMPTY = "dict(zip(COLUMNS, [[] for i in xrange(len(COLUMNS))]))"

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

    """

    def __init__(self, tax,  year, chart={}, data=[]):
        """ A Balance can be initialized by passing data as a list of tuples
        (account, amount, parent); if data is None an empty balance is created,
        and new rows can be added later by calls to add_row() method.
        
        """
        self.year = year
        self.tax = tax
        self.chart = chart
        
        # self.__data is a dictionary to keep real data, it gets converted to a
        # DataFrame only when self.df gets called.
        if isinstance(data, list):
            self.__data = {}
            for row in data:
                self.__data[row[0]] = row
            self.__to_update = True
            self.df
        elif isinstance(data, pnd.DataFrame):
            self.df = data
        else:
            raise ValueError('parameter data must be of type list or DataFrame, got %s instead' % type(data))

    def __repr__(self):
        """ pretty repr stolen from df """
        return repr(self.df)

    def __getitem__(self, item):
        """ delegate to dict """
        return self.__data[item]

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
                data = eval(EMPTY)
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
    def add(self, rows):
        """ Add rows to the balance.

        If an account is already present in self.df, the value is updated but no
        duplicates are creted.

        @ param rows: list of tuples (account, value, parent)
        
        """
        for row in rows:
            if len(row) == len(COLUMNS):               
                self.__data[row[0]] = row
            else:
                raise ValueError("Rows must be of length %s, %s received."%(len(COUMNS),len(row)))
        self.__to_update = True

    def get(self, code, default=False):
        """ Find a value by account code

        @ param code: reference year
        @ param default: default value if year is not found
        @ return: Balance

        """
        return self.__data.get(code, default)

    def pop(self, account, *args):
        """ Delete rows from the balance and returns them.

        @ param rows: list of accounts to be removed
        @ param default: default value to return if account is not present
        @ return: a dictionary
        @ raise: KeyError if account is not present
        
        """
        try:
            self.__to_update = True
            return self.__data.pop(account)
        except KeyError:
            if len(args) > 0:
                return args[0]
            raise KeyError("No account found with code '%s'" % account)

    def to_list(self):
        """ Return the balance as a list of tuples """        
        return self.__data.values()


if __name__ == '__main__':
    """ Just a test """
    mylist = [
        ('sp', 52),
        ('ce', 1200),
        ('co', 56)]
    b = Balance('123', '2012', data=mylist)
