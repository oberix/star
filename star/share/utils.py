# -*- coding: utf-8 -*-

def smartcopy(dict_):
    ''' Make a copy of a dictionary recursivly copiing any
    subdictionary or list (deep copy), but just copy the references to
    any other mutable object (shallow copy).

    @ param dict_: the dictionary to copy
    @ return: a Python dictionary
    '''
    out = {}
    for key, val in dict_.iteritems():
        if isinstance(val, (dict, list)):
            out[key] = _smartcopy(val)
        else:
            out[key] = val
    return out
