# -*- coding: utf-8 -*-
from star.share import utils
from star.share.default_meta import default_meta, default_meta_vars,\
    default_meta_graph, default_meta_graph_vars, default_meta_table,\
    default_meta_table_vars, default_meta_des, default_meta_des_vars

class MetaDict(dict):

    defaults = {}

    def __init__(self, *args, **kwargs):
        # import ipdb; ipdb.set_trace()
        if len(args) == 1 and isinstance(args[0], dict):
            kwargs = args[0]
            args = ()
        for key, val in args:
            # args elements must be tuples
            self.__setitem__(key, val)
        for key, val in kwargs.iteritems():
            self.__setitem__(key, val)
        for key, val in self.defaults.iteritems():
            try:
                self[key]
            except KeyError:
                dict.__setitem__(self, key, val)

    def __setitem__(self, key, val):
        try:
            cval = self.validate[key](val)
        except KeyError:
            raise KeyError("'%s' is not a valid md parameter.\
See metaDict.keys() for a list of valid parameters." % key)
        dict.__setitem__(self, key, cval)

    def copy(self):
        return utils.smartcopy(self)

# Dummy definitions to populate namespace, more below
class MetaDictGraph(MetaDict): pass
class MetaDictTable(MetaDict): pass
class MetaDictDes(MetaDict): pass

class MetaDictVars(MetaDict):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_vars.iteritems() ])

    def __init__(self, *args, **kwargs):
        MetaDict.__init__(self, *args, **kwargs)

class MetaDictGraphVars(MetaDict):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_graph_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_graph_vars.iteritems() ])

    def __init__(self, *args, **kwargs):
        MetaDict.__init__(self, *args, **kwargs)

class MetaDictTableVars(MetaDict):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_table_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_table_vars.iteritems() ])

    def __init__(self, *args, **kwargs):
        MetaDict.__init__(self, *args, **kwargs)

class MetaDictDesVars(MetaDict):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_des_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_des_vars.iteritems() ])

    def __init__(self, *args, **kwargs):
        MetaDict.__init__(self, *args, **kwargs)

class MetaVars(dict):
    def __setitem__(self, key, val):
        val = MetaDictVars(val)
        dict.__setitem__(self, key, val)

class MetaVarsGraph(dict):
    def __setitem__(self, key, val):
        val = MetaDictGraphVars(val)
        dict.__setitem__(self, key, val)

class MetaVarsTable(dict):
    def __setitem__(self, key, val):
        val = MetaDictTableVars(val)
        dict.__setitem__(self, key, val)

class MetaVarsDes(dict):
    def __setitem__(self, key, val):
        val = MetaDictDesVars(val)
        dict.__setitem__(self, key, val)


default_meta_graph.update({
    'vars' : [MetaVarsGraph(), MetaVarsGraph],
})

default_meta_table.update({
    'vars' : [MetaVarsTable(), MetaVarsTable],
})

default_meta_des.update({
    'vars' : [MetaVarsDes(), MetaVarsDes],
})

MetaDictGraph.validate = dict([ (key, converter) for key, (default, converter) in
                                default_meta_graph.iteritems() ])
MetaDictGraph.defaults = dict([ (key, default) for key, (default, converter) in
                                default_meta_graph.iteritems() ])

MetaDictTable.validate = dict([ (key, converter) for key, (default, converter) in
                                default_meta_table.iteritems() ])
MetaDictTable.defaults = dict([ (key, default) for key, (default, converter) in
                                default_meta_table.iteritems() ])

MetaDictDes.validate = dict([ (key, converter) for key, (default, converter) in
                              default_meta_des.iteritems() ])
MetaDictDes.defaults = dict([ (key, default) for key, (default, converter) in
                              default_meta_des.iteritems() ])

default_meta.update({
    'table': [MetaDictTable(), MetaDictTable],
    'graph': [MetaDictGraph(), MetaDictGraph], 
    'des': [MetaDictDes(), MetaDictDes], 
    'vars': [MetaVars(), MetaVars]
})

MetaDict.validate = dict([ (key, converter) for key, (default, converter) in
                           default_meta.iteritems() ])
MetaDict.defaults = dict([ (key, default) for key, (default, converter) in
                           default_meta.iteritems() ])

