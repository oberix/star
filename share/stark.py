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
import os 
import string
import copy

import pandas

from generic_pickler import GenericPickler

# pylint: disable=E1101

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__all__ = ['Stark']


STYPES = ('elab')
TYPES = [
    'D', # Dimensional
    'I', # Immutable 
    'N', # Numeric
    'C', # Currency
    'E', # Elaboration
    'R', # Rate
    ]


##########################
# Misc utility functions #
##########################

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
            names, each key contain a dictionary with the following keys:
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

    ####################
    # Magic attributes #
    ####################

    def __init__(self, df, lm=None, cod=None, stype='elab', currency='USD',
                 currdata=None):
        """
        @ param df: DataFrame
        @ param cod: save path
        @ param stype: type
        @ param lm: metadata dictionary
        @ param env: environment dictionary (usually globals() from caller)
        """
        # TODO: make a Stark form a Stark
        self._df = df
        self.cod = cod
        self._currency = currency
        self._currdata = currdata
        if stype not in STYPES:
            raise ValueError("stype must be one of %s" % STYPES)
        self.stype = stype
        if lm is None:
            lm = {}
        self._lm = lm
        self._dim = [] # Dimensions
        self._elab = [] # Elaborated
        self._num = [] # Numeric
        self._imm = [] # Immutable
        self._rate = [] # Rate
        self._curr = [] # Currency
        self._update()

    def __repr__(self):
        """ Delegate to DataFrame.__repr__().
        """
        return repr(self._df)

    def __add__(self, other):
        df = self._df.append(other.DF, ignore_index=True,
                             verify_integrity=False)
        lm = self._lm
        out_stark = Stark(df, lm=lm, cod=self.cod, stype=self.stype)
        out_stark._aggregate(inplace=True)
        return out_stark

    def __getitem__(self, key):
        ''' Delegate to DataFrame.__setitem__().
        '''
        # TODO: return a new Stark instance
        return self._df.__getitem__(key)

    def __setitem__(self, key, value):
        ''' Delegate to DataFrame.__setitem__(). The purpose of this method it
        to permit a DataFrame-like syntax when assigning a new column, while
        keeping the VD consistent.

        '''
        if isinstance(value, str) or isinstance(value, unicode):
            try:
                self._update_df(key, expr=value, var_type='E')
            except NameError:
                self._update_df(key, series=value, var_type='I')
        else: 
            self._update_df(key, series=value, var_type='N')

    def __delitem__(self, key):
        del self._df[key]
        target = _unroll(self._lm)
        target.remove(key)
        self._lm = _filter_tree(self._lm, target)

    def __len__(self):
        return len(self._df)

    ##############
    # Properties #
    ##############

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
                "df must be a pandas.DataFrame object, %s received instead",
                type(df))
        self._df = df
        # DF changed, re-evaluate calculated data
        self._update()

    # @property
    # def currency(self):
    #     return self._currency

    # @currency.setter
    # def currency(self, newcur):
    #     self.changecurr(newcur, inplace=True)

    @property
    def dim(self):
        return self._dim

    @property
    def num(self):
        return self._num

    @property
    def elab(self):
        return self._elab

    @property
    def imm(self):
        return self._imm

    @property
    def rate(self):
        return self._rate

    @property
    def curr(self):
        return self._curr

    @property
    def columns(self):
        return self._df.columns

    ######################
    # Non public methods #
    ######################

    def _update(self):
        ''' Call this method every time VD is changed to update Stark data.
        Iter over VD and fill up different lists of keys, each list contains
        names from each data type.

        ''' 
        # Start from clean lists
        self._dim = []
        self._elab = []
        self._num = []
        self._imm = []
        self._rate = []
        self._curr = []
        # Sort VD.items() by 'ORD' to have output lists already ordered.
        lm_items = self._lm.items()
        lm_items.sort(key=lambda x: x[1].get('ORD', 0))
        for key, val in lm_items:
            if val['type'] == 'D':
                self._dim += _unroll({key: val})
            elif val['type'] == 'E':
                # (Re)evaluate elab columns
                self._df[key] = self._eval(self._lm[key]['elab'])
                self._elab.append(key)
            elif val['type'] == 'N':
                # TODO: check that dtypes are really numeric types
                self._num.append(key)
            elif val['type'] == 'I':
                self._imm.append(key)
            elif val['type'] == 'C':
                self._curr.append(key)
            elif val['type'] == 'R':
                self._rate.append(key)

    def _update_lm(self, key, entry):
        ''' Update VD dictionary with a new entry.
        
        @ param key: new key in the dictionary
        @ param entry: value to assign
        @ raise ValueError: if DF/VD consistency would broke

        '''
        # Check key consistency
        self._lm[key] = entry
        self._update()

    def _update_df(self, col, series=None, var_type='N', expr=None, rlp='E', 
                   des=None, munit=None, vals=None):
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
        @ param var_type: One of lm type values, if it's 'E' an expr must not be
            None
        @ param expr: The expression to calculate the column's value, it can
            either be a string or a tuple.
        @ param des: Descriprion
        @ param munit: Unit of measure.
        @ raise ValueError: when parameters are inconsistent

        '''
        if var_type not in TYPES:
            raise ValueError("var_type mut be one of [%s]" % \
                                 '|'.join(TYPES))
        if var_type != 'E':
            self._df[col] = series

        if expr is None and var_type == 'E':
            raise ValueError(
                "You must specify an expression for var_type = 'E'")
        elif series is None and var_type != 'E':
            raise ValueError(
                "You must pass a series or list for var_type != 'E'")

        if vals is None:
            vals = pandas.DataFrame()
            
        self._update_lm(col, {
            'type' : var_type,
            'des' : des,
            'munit' : munit,
            'elab' : expr,
            'rlp' : rlp, 
            'vals': vals,
        })

    def _set_unique(self, series):
        test = pandas.unique(series)
        if len(test) > 1:
            return pandas.np.nan
        return test[0]

    def _gr_cum(self, series):
        ''' Cumulated growth rate '''
        exponent = pandas.np.log(series / 100 + 1).sum() / len(series)
        return (pandas.np.exp(exponent) - 1) * 100

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
        # Some defaults
        if dim is None:
            dim = self._dim
        if var is None:
            var = self._num + self._imm + self._elab + self._rate + self._curr
        # var and dim may be single column's name
        if isinstance(var, str) or isinstance(var, unicode):
            var = [var]
        if isinstance(dim, str) or isinstance(dim, unicode):
            dim = [dim]
        outkeys = dim + var

        if not inplace:
            df = self._df.copy()
        else:
            df = self._df
        lm = _filter_tree(self._lm, outkeys)

        # Prepare operation dictionary: for each variable set the appropriate
        # aggregation function based on its type
        operations = {}
        for name in self._num + self._curr:
            operations[name] = func
        for name in self._imm:
            operations[name] = self._set_unique
        for name in self._rate:
            operations[name] = self._gr_cum
        for name in self._elab:
            # Some elaboration need to become numeric before the aggregation,
            # others must be re-evaluated
            if lm[name].get('rlp') and lm[name]['rlp'] == 'N':
                lm[name]['type'] = 'N'
            # TODO: This is not needed if 'rlp' != 'N', but any other
            # operation seems to introduce a greater overhead to the
            # computation. This shold be invesigated further.
            operations[name] = func

        df = df.groupby(dim).aggregate(operations)[var].reset_index()

        if inplace:
            self._lm = lm
            self._update()
            return
        return Stark(df, lm=lm) # _update() gets called by __init__()

    def _find_level(self, key, value):
        ''' Tells to wich level of a dimension a value belongs
        
        @ param key: dimension name
        @ param value: value to search
        @ reutrn: level name
        @ raise: ValueError if value is not found
        '''
        df = self._lm[key]['vals']
        for col in df.columns:
            try:
                rows = df.ix[df[col] == value]
            except TypeError: 
                # If column dtype is not compatible with value type
                continue 
            if len(rows) > 0:
                return col
        raise ValueError(
            "Could not find value '%s' for key '%s'" % (value, key))

    def _eval(self, func):
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
        return eval(templ.substitute(ph_dict), {'self': self})

    ##################
    # Public methods #
    ##################

    def save(self, file_=None):
        ''' Save object as pickle file.
        
        If a filename is not provided, the one stored in self.cod will be used.

        @ param file_: destination file path 
        
        '''
        if file_ is None:
            file_ = self.cod
        if not os.path.exists(os.path.dirname(file_)):
            os.makedirs(os.path.dirname(file_))
        super(Stark, self).save(file_)

    def head(self, n=5):
        ''' Return first n elements of the DataFrame 

        @ param n: number of rows to return
        @ return: a DataFrame

        '''
        return self._df.head(n)

    def tail(self, n=5):
        ''' Return last n elements of the DataFrame 
        
        @ param n: number of rows to return
        @ return: a DataFrame

        '''
        return self._df.tail(n)

    def changecurr(self, new_curr, ts_col='YEAR'):
        ''' Change currency by appling different change rates according to
        periods.

        @ param new_curr: target currency ISO4217 code
        @ return: a new Stark instance
        @ raise ValueError: if an unknown currency is passed

        '''
        if new_curr not in self._currdata.columns:
            raise ValueError("%s is not a known currency" % new_curr)        
        lm = copy.deepcopy(self._lm)
        columns = self._df.columns
        df = self._df.join(self._currdata, on=ts_col)
        for var in self._curr:
            df[var] = df[var] * (df[new_curr] / df[self._currency])
        df = df.reset_index()[columns]
        return Stark(df, lm=lm)

    def loggit(self, var):
        # TODO: implement
        raise NotImplementedError

    def cagr(self, var, ts_col='YEAR'):
        ''' Calculate grouth rate of a variable and stores it in a new
        DataFrame column calles <variable_name>_GR. 

        cagr() works inplace.

        @ param var: variable name
        @ param ts_col: column to use as time series

        '''
        varname = '%s_GR' % var
        tmp_df = self._df[self._dim + [var]]
        try:
            tmp_df[ts_col] += 1
        except TypeError:
            # FIXME: cludgy! We should use dates instead
            tmp_df[ts_col] = tmp_df['YEAR'].map(int)
            tmp_df[ts_col] += 1
            tmp_df[ts_col] = tmp_df[ts_col].map(str)
        tmp_df.set_index(s.dim, inplace=True)
        self._df.set_index(s.dim, inplace=True)
        self._df = pandas.merge(self._df, tmp_df, left_index=True,
                                right_index=True, how='left', 
                                suffixes=('', '_tmp'))
        self._df[varname] =  100 * (self._df[var] / self._df['%s_tmp' % var] - 1)
        self._update_lm(varname, {
            'type': 'R',
            'vals': pandas.DataFrame(),
            'munit': None, # TODO: this may be set automatically if indexes
                           #       were more than strings
            'des' : None, # TODO: fill up
        })
        self._df = self._df.reset_index()[self._lm.keys()]

    def rollup(self, **kwargs):
        '''
        '''
        out_stark = Stark(self.df.copy(), lm=self._lm)
        # FIXME: keys and vals may be grouped by type in advance to minimize
        # iteretions of this loop
        for key, val in kwargs.iteritems():
            if key not in self._df.columns:
                raise ValueError("'%s' is not a dimension" % key)
            if val == 'TOT':
                out_stark.df[key] = 'TOT'
                out_stark = out_stark._aggregate()
            elif val == 'ALL':
                continue
            else:
                try:
                    level, value = val.split('.', 1)
                except ValueError:
                    # Nothing to split, get on with simple value
                    value = val
                    out_stark.df = out_stark.df.ix[out_stark.df[key] == value]
                    continue
                # We need to replace current level with target one
                vals_df = self._lm[key]['vals']
                if level not in vals_df.columns:
                    raise ValueError(
                        "'%s' is not a valid level name for column '%s'" %\
                        (level, key))
                sample_val = self._df[key].ix[0]
                curr_level = self._find_level(key, sample_val)
                out_stark.df[key] = out_stark.df[key].map(
                    vals_df.set_index(curr_level).to_dict()[level])
                out_stark = out_stark._aggregate()
                if value != 'ALL' and value != 'TOT':
                    out_stark.df = out_stark.df.ix[
                        out_stark.df[key] == value].reset_index()
        return out_stark


if __name__ == '__main__' :
    PKL_PATH = '/home/mpattaro/ercole_sorted/country_MER/1-Europa_Occidentale/AUT.pickle'
    UL_PATH = '/home/mpattaro/workspace/star/trunk/config/ercole/UL.csv'
    COUNTRY_PATH = '/home/mpattaro/workspace/star/trunk/config/ercole/PaesiUlisse.csv'
    CURR_PATH = '/home/mpattaro/workspace/star/trunk/config/ercole/CURDATA.csv'
    
    s = Stark.load(PKL_PATH)
    df = s._DF
    lm = s._VD
    ul_df = pandas.DataFrame.from_csv(UL_PATH).reset_index()
    country_df = pandas.DataFrame.from_csv(COUNTRY_PATH).reset_index()
    curr_df = pandas.DataFrame.from_csv(CURR_PATH).reset_index()

    # convert from v0.1 pickles
    for k, v in lm.iteritems():
        v['type'] = v.pop('TIP')
        if k == 'XER' or k == 'MER':
            v['vals'] = country_df
        elif k in ('X', 'M'):
            v['type'] = 'C'
        elif k == 'CODE':
            v['vals'] = ul_df
        else:
            v['vals'] = pandas.DataFrame()
    
    currdata = pandas.DataFrame.from_csv(CURR_PATH, parse_dates=False).reset_index()
    currdata['YEAR'] = currdata['YEAR'].map(str)
    currdata = currdata.set_index('YEAR')

    df['IMM'] = 100
    lm['IMM'] = {}
    lm['IMM']['type'] = 'I'
    s = Stark(df, lm=lm, currdata=currdata)
    s['TEST'] = '$X / $M'
    s['TEST_RLP'] = '$X / $M'
    lm['TEST_RLP']['rlp'] = 'N'
    
    s1 = s.changecurr('EUR')

    # s.cagr('X')
    # s1 = s.rollup(XER='AREA.1-Europa Occidentale')
    print "ok"


