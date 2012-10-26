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

STARK_TYPES = ('elab', )

TYPE_VALS = ['D', 'N', 'S', 'R']

OPERATORS = {
    '+': '__add__',
    '-': '__sub__',
    '*': '__mul__',
    '/': '__div__',
    '//': '__floordiv__',
    '**': '__pow__',
    '%': '__mod__',
}


def _unroll(dict_):
    ''' Unroll tree-like nested dictionary in depth-first order, following
    'child' keys. Siblings order can be defined with 'ORD' key.

    @ param dict_: python dictionary
    @ return: ordered list

    '''
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
    ''' Create a new tree selecting only those elements present in a list and
    keeping origninal parent-child relastionship, if a parent is missing from
    the target tree, all of it's childrens are inherited from the parent's
    parent.

    @ param meta: a dictionary 
    @ param outlist: a list of keys
    @ return: a new dictionary

    '''
    ret = dict()
    items = meta.items()
    for key, val in items:
        if key in outlist:
            ret[key] = val.copy()
            if val.get('child'):
                ret[key]['child'] = _filter_tree(val['child'], outlist)
        else:
            if val.get('child'):
                ret.update(_filter_tree(val['child'], outlist))
    return ret
 

class Stark(GenericPickler):
    ''' This is the artifact that outputs mainly from etl procedures. It is a
    collection of meta-information around datas inside a pandas DataFrame.

    Stark has the following attributes:
        DF: a pandas DataFrame
        path: the path where the object will be saved as pickle
        TYPE: type (just 'elab' for now)
        VD: a a dictionary of various info for the user; keys are DF columns
        names, each key contain a dictionary with the following keys.
            TYPE: data use, one of (D|N|S|R), that stands for:
                Dimension: can be used in aggregation (like groupby)
                Numeric: a numeric data type
                String: a string data type
                Calculated: (Ricavato in Italian)
            DES: a short description
            MIS: unit of measure
            ELAB: elaboration that ptocuced the data (if TYPE == 'R')

    '''

    def __init__(self, df, meta=None, path=None, env=None, stark_type='elab'):
        '''
        @ param df: DataFrame
        @ param path: save path
        @ param stark_type: type
        @ param meta: metadata dictionary
        @ param env: environment dictionary (usually globals() from caller)
        '''
        self._df = df.copy()
        self.path = path
        if env is None:
            self._env = globals()
        else:
            self._env = env
        if stark_type not in STARK_TYPES:
            raise ValueError("stark_type must be one of %s" % STARK_TYPES)
        self._type = stark_type
        if meta is None:
            meta = {}
        self._meta = meta
        # Call _update() to consolidate data and metadata
        # Start from clean lists
        self._update()

    def __repr__(self):
        ''' Delegate to DataFrame.__repr__().
        '''
        return repr(self._df)

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
                self.update_df(key, expr=value, var_type='R')
            except NameError:
                self.update_df(key, series=value, var_type='S')
        else: # FIXME: a type check woudn't be bad here!
            self.update_df(key, series=value, var_type='N')

    def __delitem__(self, key):
        del self._df[key]
        target = _unroll(self._meta)
        target.remove(key)
        self._meta = _filter_tree(self._meta, target)

    def __len__(self):
        return len(self._df)

    def _update(self):
        ''' Call this method every time VD is changed to update Stark data.
        Iter over VD and fill up different lists of keys, each list contains
        names from each data type.

        ''' 
        # Start from clean lists
        self._dim = list()
        self._cal = list()
        self._num = list()
        self._str = list()
        # Sort meta.items() by 'ORD' to have output lists already ordered.
        vd_items = self._meta.items()
        vd_items.sort(key=lambda x: x[1].get('ORD', 0))
        for key, val in vd_items:
            if val['TYPE'] == 'D':
                self._dim += _unroll({key: val})
            elif val['TYPE'] == 'R':
                # (Re)evaluate calculated columns
                try:
                    self._df[key] = self.eval(self._meta[key]['ELAB'])
                except AttributeError:
                    self._df[key] = self.eval_polish(self._meta[key]['ELAB'])
                self._cal.append(key)
            elif val['TYPE'] == 'N':
                # TODO: check that dtypes are really numeric types
                self._num.append(key)
            elif val['TYPE'] == 'S':
                # TODO: check that dtypes are str or unicode
                self._str.append(key)

    @property
    def meta(self):
        return self._meta

    @meta.setter
    def meta(self, meta):
        ''' VD setter:
        Just check VD/DF consistency before proceding.
        ''' 
        if meta is None:
            meta = {}
        self._meta = meta
        self._update()

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        ''' DF settre:
        Just check VD/DF consistency before proceding.
        '''
        self._df = df.copy()
        # df changed, re-evaluate calculated data
        self._update()

    def update_meta(self, key, entry):
        ''' Update VD dictionary with a new entry.
        
        @ param key: new key in the dictionary
        @ param entry: value to assign
        @ raise ValueError: if DF/VD consistency would broke

        '''
        # Check key consistency
        self._meta[key] = entry
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
        @ param var_type: One of VD TIP values, if it's 'R' an expr must not be
            None
        @ param expr: The expression to calculate the column's value, it can
            either be a string or a tuple.
        @ param des: Descriprion
        @ param mis: Unit of measure.
        @ raise ValueError: when parameters are inconsistent

        '''
        if var_type not in TYPE_VALS:
            raise ValueError("var_type mut be one of [%s]" % \
                                 '|'.join(TYPE_VALS))
        if expr is None and var_type == 'R':
            raise ValueError(
                "You must specify an expression for var_type = 'R'")
        elif series is None and var_type != 'R':
            raise ValueError(
                "You must pass a series or list for var_type != 'R'")        
        if var_type != 'R':
            self._df[col] = series
        self.update_meta(col, {
                'TYPE': var_type,
                'ORD': order,
                'DES': des,
                'MIS': mis,
                'ELAB': expr})

    def save(self, file_=None):
        ''' Save object as pickle file.
        
        If a filename is not provided, the one stored in self.path will be used.

        @ param file_: destination file path 
        
        '''
        if file_ is None:
            file_ = self.path
        if not os.path.exists(os.path.dirname(file_)):
            os.makedirs(os.path.dirname(file_))
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

    def eval_polish(self, func):
        ''' Parse and execute a statement in polish notation.

        Statemenst must be expressed in a Lisp-like manner, but uing python
        tuples. If any dataframe's column is part of the statement, the
        column's name can be expressed as a string in the statement.
        
        @ param func: function in polish notation
        @ return: function result

        Example:
            ('mul', ('div', 'B', 'C'), 100) # where 'B' and 'C' are in
                                            # df.columns
        Is the same as:
            df['B'] / df['C'] * 100

        '''
        # Some input checks
        if not hasattr(func, '__iter__'):
            raise AttributeError(
                'func must be a iterable, %s teceived instead.' % \
                    type(func).__name__)
        if len(func) < 2:
            raise AttributeError(
                'func must have at last two elements (an operator and a \
                term), received %s' % len(func))
        op = func[0]
        if op in OPERATORS.keys():
            op = OPERATORS[op]
        else:
            op = '__%s__' % func[0]
        terms = list()
        # Evaluate
        for elem in func[1:]:
            if hasattr(elem, '__iter__'): # recursive step
                terms.append(self.eval_polish(elem))
            elif elem in self._df.columns: # df col
                terms.append(self._df[elem])
            else: # literal
                terms.append(elem)
        try:
            return terms[0].__getattribute__(op)(terms[1])
        except (IndexError, TypeError):
            return terms[0].__getattribute__(op)()
            
    def aggregate(self, func='sum', dim=None, var=None):
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
        # Set up output meta
        meta = _filter_tree(self._meta, outkeys)
        return Stark(df, meta=meta, env=self._env)


if __name__ == '__main__':
    """ Test
    """ 
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
    # ... and a string column
    df['A'] = nelems * ['test']

    meta = {
        'region': {
            'TYPE': 'D',
            'child': {
                'country': {
                    'TYPE': 'D',
                    'DES': 'country',
                    'child': {
                        'city': {
                            'TYPE': 'D',
                            'DES': 'city'}}}}},
        'A': {'TYPE': 'S'},
        'B': {'TYPE': 'N',
               'ELAB': None},
        'C': {'TYPE': 'N',
               'ELAB': None},
        'D': {'TYPE': 'R',
               'ORD': 0,
               'ELAB': "$B / $C * 100"},
        'E': {'TYPE': 'R',
               'ORD': 1, 
               'ELAB': ('/', ('+', 'C', 'D'), 100)}}

    s = Stark(df, meta=meta)
    s1 = s.aggregate(numpy.sum)
