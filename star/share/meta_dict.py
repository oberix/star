# -*- coding: utf-8 -*-

from pandas import DataFrame, Series
from matplotlib import rcsetup

def validate_dict_df(dict_df):
    # TODO: implement method
    return dict_df

def validate_df(df):
    # TODO: implement method
    return df

def validate_vars(variables):
    # TODO: implement method
    return variables

def validate_elab_type(elab_type):
    # TODO: implement method
    return elab_type

def validate_munit(munit):
    # TODO: implement method
    return munit

def validate_elab(elab):
    # TODO: implement method
    return elab

def validate_rlp(rlp):
    # TODO: implement method
    return rlp

def validate_graph_type(graph_type):
    # TODO: implement method
    return graph_type

def validate_ticks(ticks):
    # TODO: implement method
    return ticks

def validate_ax(ax):
    # TODO: implement method
    return ax

def validate_cumulate(cumulate):
    # TODO: implement method
    return cumulate

def validate_formatting(formatting):
    # TODO: implement method
    return formatting

def validate_allignment(allignment):
    # TODO: implement method
    return allignment

def validate_vsep(vsep):
    # TODO: implement method
    return vsep

def validate_headers(headers):
    # TODO: implement method
    return headers

def _smartcopy(dict_):
    ''' Make a copy of a dictionary recursivly copiing any
    subdictionary or list (deep copy), but just copy the references to
    any other mutable object (shallow copy).

    @ param dict_: the dictionary to copy
    @ return: a Python dictionary
    '''
    out = {}
    for key, val in dict_.iteritems():
        if isinstance(val, dict) or isinstance(val, list) or\
           issubclass(val, dict) or issubclass(val, list):
            out[key] = _smartcopy(val)
        else:
            out[key] = val
    return out


default_meta = {
    'munit_vals': [{}, validate_dict_df],
    # Totals by groups 
    'totals': [DataFrame(), validate_df],
    'vars': [{}, validate_vars],
}

default_meta_vars = {
        'type': ['N', validate_elab_type],
        'vals': [DataFrame(), validate_df],
        'munit': ['weight.Kg', validate_munit],
        'elab': [None, validate_elab],
        # rlp is basically useless, since we can simply assign
        # a function return value and leave it to Numeric type.
        'rlp': [None, validate_rlp], # to be removed
        'label': [u'', unicode],
}

default_meta_graph = {
    'size' : [(12.0, 42.0), rcsetup.validate_nseq_float(2)],
    'fontsize': [12.0, rcsetup.validate_float],
    'title': [u'', unicode],
    'caption': [u'', unicode],
    'legend': [True, bool],
    'vars': [{}, dict]
}

default_meta_graph_vars = {
        'type': ['plot', validate_graph_type],
        'label': [u'', unicode],
        'ticklabel': [Series(), validate_ticks],
        'ax': ['sx', validate_ax],
        'color': ['#34e5ac', rcsetup.validate_color],
        'cumulate': [None, validate_cumulate],
}

default_meta_table = {
    'title': [u'', unicode],
    'caption': [u'', unicode],
    'hsep' : [False, bool],
    # pandas.Series holding fromatting metastrings
    # for rows (like 'bold', 'italics'. 'hsep', etc)
    'formatting': [None, validate_formatting],
    'vars': [{}, validate_vars]
}

defautl_meta_table_vars = {
        'order': [0, int],
        'label': [u'', unicode],
        'align': ['left', validate_allignment],
        'vsep': ['both', validate_vsep],
        'headers': [[u''], validate_headers],
}

default_meta_des = {} # TODO: define


class MetaDict(dict):
    ''' This is just an example (mostly taken from matplotlib), of how
    to extend dict applying some key validation; we actually need more
    than this for various reasons:

    1) We have to handle a deeper hierarchy than matplotlib.
    2) Some level of our hierarchy contains arbitrary keys which can
    be validated only against their data (so maybe the data shape must
    be validate against matadata instead).
    3) different subtrees have different keys, each specific subtree
    deserves it's own validation.

    Furthermore we must avoid to make unnecessary copies of big data
    containers (namely DataFrames), for this reason the use of a smart
    copy is mandatory.
    '''
    # To validate top level attributs
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta.iteritems() ])

    def __setitem__(self, key, val):
        try:
            cval = self.validate[key](val)
            dict.__setitem__(self, key, cval)
        except KeyError:
            raise KeyError('%s is not a valid md parameter.\
See metaDict.keys() for a list of valid parameters.' % key)

    def copy(self):
        return _smartcopy(self)


class MetaDictGraph(MetaDict):
    validate = dict([ (key, val) for key, val in
                      default_meta_graph.iteritems() ])

class MetaDictTable(MetaDict):
    validate = dict([ (key, val) for key, val in
                      default_meta_table.iteritems() ])

class MetaDictDes(MetaDict):
    validate = dict([ (key, val) for key, val in
                      default_meta_des.iteritems() ])
