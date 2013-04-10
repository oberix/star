# -*- coding: utf-8 -*-
#######################################################################
# Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
# Author: Marco Pattaro (<marco.pattaro@servabit.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#######################################################################

# pylint: disable=E1101,W0402
import os
import re
import string
import pandas
import numpy as np

from star.share.generic_pickler import GenericPickler

__all__ = ['Stark']

STYPES = ('elab',)
TYPES = [
    'D',  # Dimensional
    'I',  # Immutable
    'N',  # Numeric
    'C',  # Currency
    'E',  # Elaboration
    'R',  # Rate
    ]

TYPE_PATTERN = re.compile("<class \'[a-zA-Z][a-zA-Z0-9.].*\'>")

##########################
# Misc utility functions #
##########################


def _unroll(dict_):
    """ Unroll tree-like nested dictionary in depth-first order,
    following 'child' keys. Siblings order can be defined with 'ORD'
    key.

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
    """ Create a new tree selecting only those elements present in a
    list and keeping origninal parent-child relastionship, if a parent
    is missing from the target tree, all of it's childrens are
    inherited from the parent's parent.

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


def _smartcopy(dict_):
    ''' Make a copy of a dictionary recursivly copiing any
    subdictionary or list (deep copy), but just copy the references to
    any other mutable object (shallow copy).

    @ param dict_: the dictionary to copy
    @ return: a Python dictionary
    '''
    out = {}
    for key, val in dict_.iteritems():
        if isinstance(val, dict) or isinstance(val, list):
            out[key] = _smartcopy(val)
        else:
            out[key] = val
    return out


class Stark(GenericPickler):
    """ This is the artifact that outputs mainly from etl
    procedures. It is a collection of meta-information around datas
    inside a pandas DataFrame.

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
        # if stype not in STYPES:
        #     raise ValueError("stype must be one of %s" % STYPES)
        self.stype = stype
        if lm is None:
            lm = {}
        self._lm = lm
        self._dim = []  # Dimensions
        self._elab = []  # Elaborated
        self._num = []  # Numeric
        self._imm = []  # Immutable
        self._rate = []  # Rate
        self._curr = []  # Currency
        self._update()

    def __repr__(self):
        ret = repr(self._df)
        return re.sub(TYPE_PATTERN, unicode(type(self)), ret)

    def __add__(self, other):
        # Add two Stark instances. This operation imply a DataFrame.append()
        # and a Stark.rollup().
        df = self._df.append(other.df, ignore_index=True,
                             verify_integrity=False)
        lm = self.lm
        # Do not sum columns with different measure unit.
        for key in self._lm.keys():
            if self._lm[key].get('munit', None) != other.lm[key].get('munit',
                                                                     None):
                df[key] = np.nan
                lm[key]['munit'] = None
        # Create a new Stark
        out_stark = Stark(df, lm=lm, cod=self.cod, stype=self.stype,
                          currency=self._currency, currdata=self._currdata)
        out_stark._aggregate(inplace=True)
        return out_stark

    def __getitem__(self, key):
        if not isinstance(key, list):
            key = [key]
        df = self._df.__getitem__(key)
        lm = _filter_tree(self._lm, key)
        for k in key:
            if lm[k]['type'] == 'E':
                terms = self._find_elab_vars(k, lm=lm)
                for term in terms:
                    if term.strip(r'\$') not in key:
                        lm[k]['type'] = 'N'
                        break
        return Stark(df, lm=lm, currency=self._currency,
                     currdata=self._currdata)

    def __setitem__(self, key, value):
        # The purpose of this method is to permit a DataFrame-like syntax when
        # assigning a new column, while keeping the lm consistent.
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
        ''' Return a shallow copy of lm '''
        return _smartcopy(self._lm)

    @lm.setter
    def lm(self, new_lm):
        ''' lm setter:
        Just check lm/df consistency before proceding.
        '''
        if not isinstance(new_lm, dict):
            raise ValueError("lm must be a dictionry '%s' received instead" %
                             type(new_lm))
        self._lm = new_lm
        self._update()

    @property
    def df(self):
        ''' Return a copy of df selecting just those columns that have some
        metadata in lm
        '''
        return self._df[self.columns]

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
        # df changed, re-evaluate calculated data
        self._update()

    @property
    def currency(self):
        return self._currency

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
        return pandas.Index(self._lm.keys())

    @property
    def ix(self):
        return self._df.ix

    ######################
    # Non public methods #
    ######################

    def _update(self):
        ''' Call this method every time VD is changed to update Stark
        data.  Iter over VD and fill up different lists of keys, each
        list contains names from each data type.

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
        # lm_items.sort(key=lambda x: x[1].get('ORD', 0))
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
            1 - When passing an already calculated series or list to
                assign to a column, it consequently modify the LM.
            2 - When passing an expression, the new column is
                automatically calculated and assinged; finally the VD
                is updated.

        @ param col: Column's name
        @ param series: Series or list or any other type accepted as
            DataFrame column.
        @ param var_type: One of lm type values, if it's 'E' an expr
            must not be None
        @ param expr: The expression to calculate the column's value,
            it can either be a string or a tuple.
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
            'type': var_type,
            'des': des,
            'munit': munit,
            'elab': expr,
            'rlp': rlp,
            'vals': vals,
        })

    def _set_unique(self, series):
        test = series.unique()
        if len(test) > 1:
            return pandas.np.nan
        return test[0]

    def _gr_cum(self, series):
        ''' Cumulated growth rate '''
        exponent = np.log(series / 100 + 1).sum() / len(series)
        return (np.exp(exponent) - 1) * 100

    def _aggregate(self, func='sum', dim=None, var=None, inplace=False):
        ''' Apply an aggregation function to the DataFrame. If the
        DataFrame contains datas that are calculated as a
        transformation of other columns from the same DataFrame, this
        will be re-calculated in the output one.

        The user can specify which dimension should be used in the
        grouping operation and which columns must appear int the
        output DataFrame.

        @ param func: function used to aggregate, can be either a
        string or a function name.
        @ param dim: name, or list of names, of DataFrame's columns
            that act as dimensions (can be used as indexes, from
            pandas point of view).
        @ param var: name, or list of names, of DataFrame's columns
            that we want to be part of the resulting DataFrame. If
            calculated columns are in this list, also those from which
            they are evaluated must be present.
        @ return: a new Stark instance with aggregated data

        '''
        # Some defaults
        if dim is None:
            dim = self._dim
        if var is None:
            var = (self._num + self._imm + self._elab + self._rate + self._curr)
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

        # Prepare operation dictionary: for each variable set the
        # appropriate aggregation function based on its type
        operations = {}
        for name in self._num + self._curr:
            operations[name] = func
        for name in self._imm:
            operations[name] = self._set_unique
        for name in self._rate:
            operations[name] = self._gr_cum
        for name in self._elab:
            # Some elaboration need to become numeric before the
            # aggregation, others must be re-evaluated
            if lm[name].get('rlp') and lm[name]['rlp'] == 'N':
                lm[name]['type'] = 'N'
            # XXX: This is not needed if 'rlp' != 'N', but any other
            # operation seems to introduce a greater overhead to the
            # computation. This should be invesigated further.
            operations[name] = func

        df = df.groupby(dim).aggregate(operations)[var].reset_index()

        if inplace:
            self._lm = lm
            self._update()
            return
        return Stark(df, lm=lm, currency=self._currency,
                     currdata=self._currdata)

    def _find_level(self, key, value):
        ''' Tells to wich level of a dimension a value belongs

        @ param key: dimension name
        @ param value: value to search
        @ reutrn: level name
        @ raise: ValueError if value is not found
        '''
        df = self._lm[key]['vals']
        if df.empty:
            return None
        for col in df.columns:
            try:
                rows = df.ix[df[col] == value]
            except TypeError:
                # If column dtype is not compatible with value type
                continue
            if len(rows) > 0:
                return col
        raise ValueError("Could not find value '{0}' for key '{1}'"
                         "".format(value, key))

    def _find_elab_vars(self, col, lm=None):
        '''
        '''
        if lm is None:
            lm = self._lm
        expr = re.compile(r'\$[_a-zA-Z0-9]*')
        return re.findall(expr, lm[col]['elab'])

    def _suffix_elab_vars(self, col, suffix, lm=None):
        if lm is None:
            lm = self._lm
        matches = self._find_elab_vars(col, lm=lm)
        replaces = [''.join([match, suffix]) for match in matches]
        for idx, repl in enumerate(replaces):
            lm[col]['elab'] = re.sub(r'\%s' % matches[idx], repl,
                                     lm[col]['elab'])
        return lm

    def _eval(self, func):
        ''' Evaluate a function with DataFrame columns'es placeholders.

        Without placeholders this function is just a common python
        eval; when func contains column's names preceded by '$', this
        will be substituted with actual column's reference before
        passing the whole string to eval().

        @ param func: a string rappresenting a valid python statement;
            the string can containt DataFrame columns'es placeholders
            in the form of '$colname'
        @ return: eval(func) return value

        Example:
            "$B / $C * 100"

        '''
        if not isinstance(func, str) or isinstance(func, unicode):
            raise AttributeError('func must be a string, {0} received instead.'
                                 ''.format(type(func).__name__))
        templ = string.Template(func)
        ph_dict = dict()
        ph_list = [ph[1] for ph in string.Template.pattern.findall(func)]  #@UndefinedVariable
        for ph in ph_list:
            ph_dict[ph] = str().join(["self._df['", ph, "']"])
        return eval(templ.substitute(ph_dict), {'self': self, 'np': np})

    def _logit(self, var, how='mean', upper=100.0, prec=0.9):
        ''' This is the real logit implementation, the logit() just
        repare the Stark for a later evaluation at update time
        '''
        if prec <= 0 or prec >= 1:
            raise ValueError("prec must be in the range (0, 1), %s received "
                             "instead" % prec)
        if upper <= 0:
            raise ValueError("upper must be a positive float, %s received "
                             "instead" % upper)
        med = 0.0
        distance = 0.0
        if how == 'mean':
            med = self._df[var].mean()
            distance = np.std(self._df[var])
        elif how == 'median':
            med = self._df[var].median()
            quant = (self._df[var].quantile(q=0.25),
                     self._df[var].quantile(q=0.75))
            distance = min((med - quant[0]), (quant[1] - med))
        else:
            raise ValueError("parameter 'how' can be one of ['mean' | "
                             "'median'], '%s' received instead" % how)
        beta = -np.log(1 / prec - 1) / distance
        alpha = med * (-beta)
        return upper / (1 + np.exp(alpha - beta * self._df[var]))

    def _rollup(self, df, **kwargs):
        select = {}
        subs = {}
        # decide actions
        for key, val in kwargs.iteritems():
            splitted = val.split('.', 1)
            vals_df = self._lm[key]['vals']
            if len(splitted) == 1 or (len(splitted) > 1 and
                                      splitted[0] not in vals_df.columns):
                if val == 'ALL':
                    continue
                elif val == 'TOT':
                    idx = df[key].unique()
                    subs[key] = pandas.Series(['TOT'] * len(idx), index=idx)
                else:
                    curr_level = self._find_level(key, self._df[key].ix[0])
                    next_level = self._find_level(key, val)
                    if curr_level and next_level and curr_level != next_level:
                        subs[key] = vals_df.set_index(curr_level,
                                                      verify_integrity=False)\
                                .to_dict()[next_level]
                    select[key] = val
            elif len(splitted) > 1:
                val = splitted[1]
                curr_level = self._find_level(key, self._df[key].ix[0])
                next_level = splitted[0]
                if curr_level and next_level and curr_level != next_level:
                    subs[key] = vals_df.set_index(curr_level,
                                                  verify_integrity=False)\
                            .to_dict()[next_level]
                select[key] = val
            else:  # pragma: no cover
                raise ValueError  # be more specific!

        # substitute
        print(subs)
        for key, val in subs.iteritems():
            df[key] = df[key].map(val)
        # select
        conditions = [(df[key] == val) for key, val in select.iteritems()]
        mask = pandas.Series([True] * len(df))
        print("0: {0}".format(df))
        for condition in conditions:
            mask &= condition
        print(mask)
        print("1: {0}".format(df[mask]))
        return df[mask]

    ##################
    # Public methods #
    ##################

    def save(self, file_=None):
        ''' Save object as pickle file.

        If a filename is not provided, the one stored in self.cod will
        be used.

        @ param file_: destination file path

        '''
        if file_ is None:
            file_ = self.cod
        if not os.path.exists(os.path.dirname(file_)):
            os.makedirs(os.path.dirname(file_))

#        self._df = self._df.set_index(self.dim).to_sparse()
        super(Stark, self).save(file_)
#        self._df = self._df.to_dense().reset_index()

#    @classmethod
#    def load(self, file_):
#        return super(Stark, self).load(file_)
#        ret = super(Stark, self).load(file_)
#        try:
#            ret._df = ret._df.to_dense().reset_index()
#        except:
#            pass
#        return ret

    def head(self, n=5):
        ''' Return first n elements of the DataFrame

        @ param n: number of rows to return
        @ return: a DataFrame

        '''
        lm = self.lm
        return Stark(self._df.head(n), lm=lm, currency=self._currency,
                     currdata=self._currdata)

    def tail(self, n=5):
        ''' Return last n elements of the DataFrame

        @ param n: number of rows to return
        @ return: a DataFrame

        '''
        lm = self.lm
        return Stark(self._df.tail(n), lm=lm, currency=self._currency,
                     currdata=self._currdata)

    def merge(self, other, how='left', sort=False, lsuffix='_x', rsuffix='_y'):
        ''' Merge Stark objects by performing a database-style join
        operation by dimensions.

        @ param other: A Stark object wich dimensional variables are a
            subset of the current Stark.
        @ param how: {'left', 'right', 'outer', 'inner'}
            How to handle indexes of the two objects. Default: 'left'
            for joining on index, None otherwise
            * left: use calling frame's index
            * right: use input frame's index
            * outer: form union of indexes
            * inner: use intersection of indexes
        @ param lsuffix: Suffix to use from left frame's overlapping
            columns.
        @ param rsuffix: Suffix to use from right frame's overlapping
            colums.
        @ param sort: boolean, default False Order result Stark
            lexicographically by the join key. If False, preserves the
            index order of the calling (left) Stark
        @ return: a new Stark instance.

        '''
        if not set(other.dim).issubset(self.dim):
            raise ValueError("other's dimensions must be subset of the current "
                             "Stark dimensions")
        # use multi-index to perform a join
        self._df.set_index(self.dim, inplace=True)
        other._df.set_index(other.dim, inplace=True)
        out_df = self._df.join(other._df, how=how, sort=sort, lsuffix=lsuffix,
                               rsuffix=rsuffix).reset_index()

        # prepare output lm
        out_lm = self.lm
        for col in out_df.columns:
            # handle suffixed variables
            if col.endswith(lsuffix):
                out_lm[col] = out_lm.pop(col.strip(lsuffix))
                if out_lm[col]['type'] == 'E':
                    # elab_vars(col, lsuffix)
                    self._suffix_elab_vars(col, lsuffix, lm=out_lm)
            elif col.endswith(rsuffix):
                out_lm[col] = other.lm[col.strip(rsuffix)]
                if out_lm[col]['type'] == 'E':
                    # elab_vars(col, rsuffix)
                    self._suffix_elab_vars(col, rsuffix, lm=out_lm)
            # copy other's variables
            if col not in out_lm.keys():
                out_lm[col] = other.lm[col]

        # pack up everything and return
        self._df = self._df.reset_index()
        other.df = other._df.reset_index()
        return Stark(out_df, lm=out_lm)

    def changecurr(self, new_curr, ts_col='YEAR'):
        ''' Change currency by appling different change rates according to
        periods.

        @ param new_curr: target currency ISO4217 code
        @ return: a new Stark instance
        @ raise ValueError: if an unknown currency is passed

        '''
        if new_curr not in self._currdata.columns:
            raise ValueError("%s is not a known currency" % new_curr)
        lm = _smartcopy(self._lm)
        columns = self._df.columns
        df = self._df.join(self._currdata, on=ts_col)
        for var in self._curr:
            df[var] = df[var] * (df[new_curr] / df[self._currency])
        df = df.reset_index()[columns]
        return Stark(df, lm=lm, currency=new_curr, currdata=self._currdata)

    def logit(self, var, how='mean', upper=100.0, prec=0.9):
        ''' Calculate the logistic distribution of a DataFrame variable and
        stores it in a new variable called <var>_LOGIT.

        @ param var: Name of the Series in the df to evaluate lgistic
        @ param how: 'mean' or 'median', method used to estimate
            distribution simmetry
        @ param upper:  upper asintotic bound
        @ param prec: precision percent. This is the slice of y value
            to limit the evauation to, it must be in the intervall
           (0, 1)
        '''
        key = '%s_LOGIT' % var
        # self._df[key] = self._logit(var, how, upper, prec)
        self._update_lm(
            key=key,
            entry={
                'type': 'E',
                'rlp': 'E',
                'elab': "self._logit('%s', how='%s', upper= %s, prec=%s)" %\
                (var, how, upper, prec),
            })

    def setun(self, var, **kwargs):
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
            tmp_df[ts_col] = tmp_df[ts_col].map(int)
            tmp_df[ts_col] += 1
            tmp_df[ts_col] = tmp_df[ts_col].map(str)
        tmp_df.set_index(self.dim, inplace=True)
        self._df.set_index(self.dim, inplace=True)
        self._df = pandas.merge(self._df, tmp_df, left_index=True,
                                right_index=True, how='left',
                                suffixes=('', '_tmp'))
        self._df[varname] = (100 * (self._df[var] /
                                    self._df['%s_tmp' % var] - 1))
        self._update_lm(varname, {
            'type': 'R',
            'vals': pandas.DataFrame(),
            'munit': None,  # TODO: this may be set automatically if indexes
                            #       were more than strings
            'des': None,  # TODO: fill up
        })
        self._df = self._df.reset_index()[self._lm.keys()]

    def rollup(self, **kwargs):
        """
        """
        # FIXME: find a way to avoid this copy, perhaphs _aggregate()
        # should be called inside _rollup() only when it's really
        # needed.
        tmp_df = self._df.copy()
        self._df = self._rollup(self._df, **kwargs)
        ret = self._aggregate()
        self._df = tmp_df
        return ret
