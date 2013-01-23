# -*- coding: utf-8 -*-
from pandas import DataFrame, Series
# some validation is already implemented
from matplotlib import rcsetup

ELAB_TYPES = [
    'D', # Dimensional
    'I', # Immutable
    'N', # Numeric
    'C', # Currency
    'E', # Elaboration
    'R', # Rate
    ]

'''
Following functions should all return the input parameters or rise a
ValueError is this is not of the expected type or form.
'''

def validate_dict_df(dict_df):
    # TODO: implement method
    return dict_df

def validate_df(df):
    if not isinstance(df, DataFrame):
        raise ValueError("Object must be a pandas.DataFrame")
    return df

def validate_elab_type(elab_type):
    if elab_type not in ELAB_TYPES:
        raise ValueError("'type' must be one of (%s)" % '|'.join(ELAB_TYPES))
    return elab_type

def validate_table_type(table_type):
    # TODO: implement method
    return table_type

def validate_munit(munit):    
    # XXX: This could be a consistency check against munit vals
    return unicode(munit)

def validate_elab(elab):
    # XXX: could be better, but at last this avoid the insertion of
    # wierd charachters.
    return str(elab)

def validate_rlp(rlp):
    # TODO: implement method
    return rlp

def validate_graph_type(graph_type):
    from star.remida import plotters
    avaiables = [plotter for plotter in dir(plotters) 
                          if not plotter.startswith('_')] + ['lax']
    if graph_type not in avaiables:
        raise ValueError("'%s' is not a valid plotter, currenttly \
aviable plotters are (%s)" % (graph_type, '|'.join(avaiables)))
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

def validate_float_format(format):
    # TODO: implement method
    return format

def validate_bool(var):
    if isinstance(var, (str, unicode)):
        var = var.lower()
    if var in ('t', True, 'true', 1):
        return True
    elif var in ('f', False, 'false', 0):
        return False
    else:
        raise ValueError("'%s' is not a valid boolean" % var)

default_meta = {
    'munit_vals': [{}, validate_dict_df], # This looks similar to vars
    # Totals by groups 
    'totals': [DataFrame(), validate_df],
}

default_meta_vars = {
    'type': ['N', validate_elab_type],
    'vals': [DataFrame(), validate_df],
    'des': [u'', unicode],
    'munit': ['', validate_munit],
    'elab': [None, validate_elab],
    'rlp': [None, validate_rlp], # to be removed
    'label': [u'', unicode],
}

default_meta_graph = {
    'size' : [(3.2, 2.0), rcsetup.validate_nseq_float(2)],
    'fontsize': [12.0, rcsetup.validate_float],
    'title': [u'', unicode],
    'caption': [u'', unicode],
    'legend': [True, validate_bool],
    'footnote': [u'', unicode],
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
    'footer': [u'', unicode],
    'just_data': [False, validate_bool],
    'type': ['tab', validate_table_type],
    'hsep' : [False, validate_bool],
    # pandas.Series holding fromatting metastrings
    # for rows (like 'bold', 'italics'. 'hsep', etc)
    'formatting': [None, validate_formatting],
}

default_meta_table_vars = {
    'order': [0, int],
    'label': [u'', unicode],
    'align': [u'left', validate_allignment],
    'vsep': [u'both', validate_vsep],
    'headers': [[u''], validate_headers],
    'float_format': [u'{0:.3f}', validate_float_format],
}

default_meta_des = {} # TODO: define
default_meta_des_vars = {} # TODO: define
