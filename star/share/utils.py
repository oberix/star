# -*- coding: utf-8 -*-

def unroll(dict_):
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
            ret += unroll(val['child'])
    return ret

def filter_tree(meta, outlist):
    """ Create a new tree selecting only those elements present in a
    list and keeping origninal parent-child relastionship, if a parent
    is missing from the target tree, all of it's childrens are
    inherited from the parent's parent.

    @ param meta: a dictionary or dictionary subclass instance
    @ param outlist: a list of keys
    @ return: a new dictionary

    """
    ret = meta.__class__()
    items = meta.items()
    for key, val in items:
        if key in outlist:
            ret[key] = val.copy()
            if val.get('child'):
                ret[key]['child'] = filter_tree(val['child'], outlist)
        elif val.get('child'):
            ret.update(filter_tree(val['child'], outlist))
    return ret

def smartcopy(dict_):
    ''' Make a copy of a dictionary recursivly copiing any
    subdictionary or list (deep copy), but just copy the references to
    any other mutable object (shallow copy).

    @ param dict_: the dictionary to copy (or dictionary subclass)
    @ return: a Python dictionary
    '''
    out = dict_.__class__()
    for key, val in dict_.iteritems():
        if isinstance(val, dict):
            out[key] = smartcopy(val)
        else:
            out[key] = val
    return out
