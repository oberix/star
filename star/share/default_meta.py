# -*- coding: utf-8 -*-
from pandas import DataFrame, Series
# some validation is already implemented
from matplotlib import rcsetup

'''
Following functions should all return the input parameters or rise a
ValueError is this is not of the expected type or form.
'''

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

default_meta = {
    'munit_vals': [{}, validate_dict_df], # This looks similar to vars
    # Totals by groups 
    'totals': [DataFrame(), validate_df],
#    'vars': [{}, validate_vars],
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
#    'vars': [{}, dict],
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
#    'vars': [{}, validate_vars],
}

default_meta_table_vars = {
    'order': [0, int],
    'label': [u'', unicode],
    'align': ['left', validate_allignment],
    'vsep': ['both', validate_vsep],
    'headers': [[u''], validate_headers],
}

default_meta_des = {} # TODO: define
default_meta_des_vars = {} # TODO: define
