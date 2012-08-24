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
from datetime import datetime

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share.generic_pickler import GenericPickler
from balance import Balance
from balance import COLUMNS as BCOLUMNS

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'
__all__ = ['Company']

COLUMNS = BCOLUMNS + ['tax', 'year']

class Company(GenericPickler):
    """ A Company is an aggregation of Balances.

    A company has the following attributes:
        - name: Name of the company
        - create_date: date when the object has been created
        - df: a DataFrame containing balances datas

    It provides the following methods:
        - add(): to add a new balance to the Company
        - get(): to retrive an already present Balance
        - pop(): to remove a Balance
        
    """

    def __init__(self, name, balances=[]):
        """ Set initials Values ad assign a create_date.

        @ param tax: TAX/VAT code
        @ param name: company name
        @ param balances: list of Balance objects to fill the company with

        """
        self._create_date = datetime.now()
        self.__data = {}
        
        self.name = name
        self.add(balances)
        self.df

    def __repr__(self):
        """ pretty repr stolen from df """
        return repr(self.df)

    def __getitem__(self, item):
        """ delegate to dict """
        return self.__data[item]

    # Getters and Setters

    @property
    def df(self):
        """ __df getter

        self.__df holds the DataFrame containing all balances data of hte
        company over the years.

        Since a DataFrame is easy to query, but hard (impossible) to modify in
        place, the update of this attribute is 'lazy', just when this method is
        called, however ths self.__df variable is kept as a cache, not necessary
        calculated every time. Remember to set 'self.__to_update = True'
        whenever you implement a method that should cause the self.__df update.

        """
        if self.__to_update is True:
            # prepare an empty dictionary with COLUMNS elements as keys and
            # empty lists as values
            data = dict(zip(COLUMNS, [[] for i in xrange(len(COLUMNS))]))
            if len(self.__data) > 0:
                for acc in self.__data.itervalues():
                    acc_list = acc.to_list()
                    for row in acc_list:
                        # FIXME: this does not look at COLUMNS values, thus
                        # changing it would brake the module.
                        data['tax'].append(acc.tax)
                        data['year'].append(acc.year)
                        data['account'].append(row[0])
                        data['amount'].append(row[1])
            self.__df = pnd.DataFrame(data, columns=COLUMNS)
            self.__to_update = False
        return self.__df

    @df.setter
    def df(self, df):
        """ df setter

        When assigning a DataFrame to a Company instance, we have to re-evaluate
        raw data from the DataFrame; basically this is the inverse of df.getter.
        
        """
        if df.columns.tolist() == COLUMNS:
            years = df.ix['year'].groupby('year')
            for year in years:
                self.__data = Balance(self.tax, year, data=df.xs(BCOLUMNS))
        else:
            raise ValueError('DataFrame must have the following columns: %s' % COLUMNS)
        self.__to_update = False

    @property
    def create_date(self):
        """ Creation date getter
        create_date shold remain read-only
        """
        return self._create_date

    # Public

    def add(self, balances):
        """ Add a balance to the Company

        @ param balance: the Balance object to add

        """
        if hasattr(balances, 'year'):
            self.__data[balances.year] = balances
        else:
            for balance in balances:
                self.__data[balance.year] = balance
        self.__to_update = True

    def get(self, year, default=False):
        """ Find a balance by year

        @ param year: reference year
        @ param default: default value if year is not found
        @ return: Balance

        """
        return self.__data.get(year, default)

    def pop(self, year, *args):
        """ Remove a balance and return it

        @ param year: reference year
        @ return: Balance
        @ raise KeyError

        """
        try:
            self.__to_update = True
            return self.__data.pop(year)
        except KeyError:
            if len(args) > 0:
                return args[0]
            raise KeyError("No Balance found or year '%s'" % year)

    def to_list(self):
        """ Return the company as a list of tuples """        
        return self.__data.values()


if __name__ == "__main__":
    """ Just a test """
    
    blist1 = [
        ('sp', 52),
        ('ce', 1200),
        ('co', 56)]
    blist2 = [
        ('sp', 2),
        ('ce', 4),
        ('co', 8)]
    b1= Balance('123', '2012', data=blist1)
    b2= Balance('123', '2013', data=blist2)
    print "Loading company"
    c = Company('US Robotics & Mechanical Man Corp.', balances=[b1, b2])
    print c
    print "Adding balance"
    c.add(b1)
    print c
    print "Get balance 2012"
    c.get('2012')
    print c
    print "Pop Balance 2013"
    c.pop('2013')
    print c
    # pickle test
#    fd = open('/tmp/test.pickle', 'w')
    c.save('/tmp/test.pickle')
#    fd.close()
#    fd = open('/tmp/test.pickle', 'r')
    c1 = Company.load('/tmp/test.pickle')
#    fd.close()
