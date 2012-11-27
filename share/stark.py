# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__all__ = ['Stark']

import os 
import pandas
import numpy
import string

from generic_pickler import GenericPickler

STYPES = ('elab')
TYPES = [
    'D', # Dimensional
    'I', # Immutable 
    'N', # Numeric
    'C', # Currency
    'E', # Elaboration
    'R', # Rate
    ]


def _unroll(dict_):
    """ Unroll tree-like nested dictionary in depth-first order, following
    'child' keys. Siblings order can be defined with 'ORD' key.

    @ param dict_: python dictionary
    @ return: ordered list

    """
    ret = list()
    # Sort items to preserve order between siblings
    items = dict_.items()
    items.sort(key=lambda x: x[1].get('ORD', 0))
    for key, val in items:
        ret.append(key)
        if val.get('child'):
            ret += _unroll(val['child'])
    return ret

def _filter_tree(meta, outlist):
    """ Create a new tree selecting only those elements present in a list and
    keeping origninal parent-child relastionship, if a parent is missing from
    the target tree, all of it's childrens are inherited from the parent's
    parent.

    @ param meta: a dictionary 
    @ param outlist: a list of keys
    @ return: a new dictionary

    """
    ret = dict()
    items = meta.items()
    for key, val in items:
        if key in outlist:
            ret[key] = val.copy()
            if val.get('child'):
                ret[key]['child'] = _filter_tree(val['child'], outlist)
        elif val.get('child'):
            ret.update(_filter_tree(val['child'], outlist))
    return ret
 

class Stark(GenericPickler):
    """ This is the artifact that outputs mainly from etl procedures. It is a
    collection of meta-information around datas inside a pandas DataFrame.

    Stark has the following attributes:
        df: a pandas DataFrame
        cod: the path where the object will be saved as pickle
        stype: type (just 'elab' for now)
        lm: a a dictionary of various info for the user; keys are df columns
        names, each key contain a dictionary with the following keys.
            type: data use, one of (D|N|S|R), that stands for:
                Dimension: can be used in aggregation (like groupby)
                Numeric: a numeric data type
                String: a string data type
                Calculated: (Ricavato in Italian)
            des: a short description
            vals: values that the variables can assume
            munit: unit of measure
            elab: elaboration that ptocuced the data (if TIP == 'R')
            dtype: shortcut to np.dtype (?)
    """

    def __init__(self, df, lm=None, cod=None, stype='elab'):
        """
        @ param df: DataFrame
        @ param cod: save path
        @ param stype: type
        @ param lm: metadata dictionary
        @ param env: environment dictionary (usually globals() from caller)
        """
        self._df = df
        self.cod = cod
        if stype not in STYPES:
            raise ValueError("stype must be one of %s" % STYPES)
        self.stype = stype
        if lm is None:
            lm = {}
        self._lm = lm
        self._update()

    def __repr__(self):
        """ Delegate to DataFrame.__repr__().
        """
        return repr(self._df)

    def __add__(self, other):
        df = self._df.append(other.DF, ignore_index=True, verify_integrity=False)
        lm = self._lm
        out_stark = Stark(df, lm=lm, cod=self.cod, stype=self.stype)
        out_stark._aggregate(inplace=True)
        return out_stark

    def __getitem__(self, key):
        ''' Delegate to DataFrame.__setitem__().
        '''
        return self._df.__getitem__(key)

    def __setitem__(self, key, value):
        ''' Delegate to DataFrame.__setitem__(). The purpose of this method it
        to permit a DataFrame-like syntax when assigning a new column, while
        keeping the VD consistent.

        '''
        if isinstance(value, str) or isinstance(value, unicode):
            try:
                self.update_df(key, expr=value, var_type='E')
            except NameError:
                self.update_df(key, series=value, var_type='I')
        else: # TODO: a type check woudn't be bad here!
            self.update_df(key, series=value, var_type='N')

    def __delitem__(self, key):
        del self._df[key]
        target = _unroll(self._lm)
        target.remove(key)
        self._lm = _filter_tree(self._lm, target)

    def __len__(self):
        return len(self._df)

    def _update(self):
        ''' Call this method every time VD is changed to update Stark data.
        Iter over VD and fill up different lists of keys, each list contains
        names from each data type.

        ''' 
        # Start from clean lists
        self._dim = list() # dimensions
        self._cal = list() # 
        self._num = list()
        self._str = list()
        # Sort VD.items() by 'ORD' to have output lists already ordered.
        vd_items = self._lm.items()
        vd_items.sort(key=lambda x: x[1].get('ORD', 0))
        for key, val in vd_items:
            if val['type'] == 'D':
                self._dim += _unroll({key: val})
            elif val['type'] == 'R':
                # (Re)evaluate calculated columns
                try:
                    self._df[key] = self.eval(self._lm[key]['elab'])
                except AttributeError:
                    self._df[key] = self.eval_polish(self._lm[key]['elab'])
                self._cal.append(key)
            elif val['type'] == 'N':
                # TODO: check that dtypes are really numeric types
                self._num.append(key)
            elif val['type'] == 'S':
                # TODO: check that dtypes are str or unicode
                self._str.append(key)

    @property
    def lm(self):
        return self._lm

    @lm.setter
    def lm(self, vd):
        ''' VD setter:
        Just check VD/DF consistency before proceding.
        ''' 
        if vd is None:
            vd = {}
        self._lm = vd
        self._update()

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        ''' DF settre:
        Just check VD/DF consistency before proceding.
        '''
        if not isinstance(df, pandas.DataFrame):
            raise TypeError(
                "df must be a pandas.DataFrame object, %s received instead", type(df))
        self._df
        # DF changed, re-evaluate calculated data
        self._update()

    @property
    def dim(self):
        return self._dim

    @property
    def num(self):
        return self._num

    @property
    def cal(self):
        return self._cal

    @property
    def columns(self):
        return self._df.columns

    def update_lm(self, key, entry):
        ''' Update VD dictionary with a new entry.
        
        @ param key: new key in the dictionary
        @ param entry: value to assign
        @ raise ValueError: if DF/VD consistency would broke

        '''
        # Check key consistency
        self._lm[key] = entry
        self._update()

    def update_df(self, col, series=None, var_type='N', expr=None, des=None,
                  mis=None, order=0):
        ''' Utility method to safely add/update a DataFrame column.
        
        Add or modify a column of the DataFrame trying to preserve DF/VD
        consistency. This method has two main beheviours:
            1 - When passing an already calculated series or list to assign to
                a column, it consequently modify the VD.
            2 - When passing an expression, the new column is automatically
                calculated and assinged; finally the VD is updated.

        @ param col: Column's name
        @ param series: Series or list or any other type accepted as DataFrame
            column.
        @ param var_type: One of VD type values, if it's 'R' an expr must not be
            None
        @ param expr: The expression to calculate the column's value, it can
            either be a string or a tuple.
        @ param des: Descriprion
        @ param mis: Unit of measure.
        @ raise ValueError: when parameters are inconsistent

        '''
        if var_type not in TYPES:
            raise ValueError("var_type mut be one of [%s]" % \
                                 '|'.join(TYPES))
        if expr is None and var_type == 'R':
            raise ValueError(
                "You must specify an expression for var_type = 'R'")
        elif series is None and var_type != 'R':
            raise ValueError(
                "You must pass a series or list for var_type != 'R'")        
        if var_type != 'R':
            self._df[col] = series
        self.update_vd(col, {
                'type' : var_type,
                'ORD' : order,
                'des' : des,
                'MIS' : mis,
                'elab' : expr})

    def save(self, file_=None):
        ''' Save object as pickle file.
        
        If a filename is not provided, the one stored in self.cod will be used.

        @ param file_: destination file path 
        
        '''
        if file_ is None:
            file_ = self.cod
        if not os.path.exists(os.path.dirname(file_)):
            os.makedirs(os.path.dirname(file_))
        self._env = None # cannot pickle finctions declared outside this scope
        super(Stark, self).save(file_)

    def eval(self, func):
        ''' Evaluate a function with DataFrame columns'es placeholders.
        
        Without placeholders this function is just a common python eval; when
        func contains column's names preceded by '$', this will be substituted
        with actual column's reference before passing the whole string to
        eval().


        @ param func: a string rappresenting a valid python statement; the
            string can containt DataFrame columns'es placeholders in the form
            of '$colname'
        @ return: eval(func) return value

        Example:
            "$B / $C * 100"
        
        '''
        if not isinstance(func, str) or isinstance(func, unicode):
            raise AttributeError(
                'func must be a string, %s received instead.' % \
                    type(func).__name__)
        templ = string.Template(func)
        ph_dict = dict()
        ph_list = [ph[1] for ph in string.Template.pattern.findall(func)]
        for ph in ph_list:
            ph_dict[ph] = str().join(["self._df['", ph, "']"])
        return eval(templ.substitute(ph_dict), self._env, {'self': self})
            
    def _aggregate(self, func='sum', dim=None, var=None, inplace=False):
        ''' Apply an aggregation function to the DataFrame. If the DataFrame
        contains datas that are calculated as a transformation of other columns
        from the same DataFrame, this will be re-calculated in the output one.

        The user can specify which dimension should be used in the grouping
        operation and which columns must appear int the output DataFrame.

        @ param func: function used to aggregate, can be either a string or a
            function name.
        @ param dim: name, or list of names, of DataFrame's columns that act as
            dimensions (can be used as indexes, from pandas point of view).
        @ param var: name, or list of names, of DataFrame's columns that we
            want to be part of the resulting DataFrame. If calculated columns
            are in this list, also those from which they are evaluated must be
            present.
        @ return: a new Stark instance with aggregated data

        '''
        if dim is None:
            dim = self._dim
        if var is None:
            var = self._num + self._cal 
        # var and dim may be single column's name
        if isinstance(var, str) or isinstance(var, unicode):
            var = [var]
        if isinstance(dim, str) or isinstance(dim, unicode):
            dim = [dim]
        outkeys = dim + var
        group = self._df.groupby(dim)
        # Create aggregate df
        # Trying to avoid dispatching ambiguity
        try:
            df = group.aggregate(func)[var].reset_index()
        except AttributeError:
            df = group.aggregate(eval(func))[var].reset_index()
        # Set up output VD
        vd = _filter_tree(self._lm, outkeys)
        if inplace:
            self._df = df
            self._lm = vd
            self._update()
            return
        return Stark(df, lm=vd, env=self._env)

    def rollup(self, **kwargs):
        # TODO: implement (calling _aggregate)
        raise NotImplementedError
    

if __name__ == '__main__' :
    ''' Test
    ''' 
    cols = ['B', 'C']
    countries = numpy.array([
        ('namerica', 'US', 'Washington DC'),
        ('namerica', 'US', 'New York'),
        ('europe', 'UK', 'London'),
        ('europe', 'UK', 'Liverpool'),
        ('europe', 'GR', 'Athinai'),
        ('europe', 'GR', 'Thessalonica'),
        ('europe', 'IT', 'Roma'),
        ('europe', 'IT', 'Milano'),
        ('asia', 'JP', 'Tokyo'),
        ('samerica', 'BR', 'Brasilia'),
        ('samerica', 'BR', 'Rio'),
        ])
    nelems = 100
    key = map(tuple, countries[
            numpy.random.randint(0, len(countries), nelems)])
    index = pandas.MultiIndex.from_tuples(key, names=[
            'region', 'country', 'city'])

    # DataFrame with two numeric columns...
    df = pandas.DataFrame(
        numpy.random.randn(nelems, len(cols)), columns=cols,
        index=index).sortlevel().reset_index()
    df1 = pandas.DataFrame(
        numpy.random.randn(nelems, len(cols)), columns=cols,
        index=index).sortlevel().reset_index()
    # ... and a string column
    df['A'] = nelems * ['test']
    df1['A'] = nelems * ['test']

    vd = {
        'region' : {
            'type': 'D',
            'child': {
                'country': {
                    'type': 'D',
                    'des': 'country',
                    'child': {
                        'city': {
                            'type': 'D',
                            'des': 'city'}
                        }
                    }
                }
            },
        'A' : {'type': 'S'},
        'B' : {'type': 'N',
               'elab': None,},
        'C' : {'type': 'N',
               'elab': None,},
        'D' : {'type': 'R',
               'ORD': 0,
               'elab': "$B / $C * 100"},
        'E' : {'type': 'R',
               'ORD': 1, 
               'elab': ('/', ('+', 'C', 'D'), 100)},
        'F': {'type': 'I'}
        }

    vd1 = {
        'region' : {
            'type': 'D',
            'child': {
                'country': {
                    'type': 'D',
                    'des': 'country',
                    'child': {
                        'city': {
                            'type': 'D',
                            'des': 'city'}
                        }
                    }
                }
            },
        'A' : {'type': 'S'},
        'B' : {'type': 'N',
               'elab': None,},
        'C' : {'type': 'N',
               'elab': None,},
        'D' : {'type': 'R',
               'ORD': 0,
               'elab': "$B / $C * 100"},
        'E' : {'type': 'R',
               'ORD': 1, 
               'elab': ('/', ('+', 'C', 'D'), 100)},
        }


    s = Stark(df, lm=vd, env=globals())
    s1 = Stark(df1, lm=vd1, env=globals())
