# -*- coding: utf-8 -*-
from star.share import utils
from star.share.default_meta import default_meta, default_meta_vars,\
    default_meta_graph, default_meta_graph_vars, default_meta_table,\
    default_meta_table_vars, default_meta_des, default_meta_des_vars

'''
Meta
    MetaVars
        MetaVarsAttr
    MetaGraph
        MetaVarsGraph
            MetaVarsAttrGraph
    MetaTable
        MetaVarsTable
            MetaVarsAttrTable
    MetaDes
        MetaVarsDes
            MetaVarsAttrDes
'''

class Meta(dict):

    defaults = {} # Just a temporary placeholder

    def __init__(self, *args, **kwargs):
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
            raise KeyError("'%s' is not a valid md parameter. \
See metaDict.keys() for a list of valid parameters." % key)
        dict.__setitem__(self, key, cval)

    def copy(self):
        return utils.smartcopy(self)

# Dummy definitions to populate namespace, more below
class MetaGraph(Meta): pass
class MetaTable(Meta): pass
class MetaDes(Meta): pass

class MetaVarsAttr(Meta):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_vars.iteritems() ])

class MetaVarsAttrGraph(Meta):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_graph_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_graph_vars.iteritems() ])

class MetaVarsAttrTable(Meta):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_table_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_table_vars.iteritems() ])

class MetaVarsAttrDes(Meta):
    validate = dict([ (key, converter) for key, (default, converter) in
                      default_meta_des_vars.iteritems() ])
    defaults = dict([ (key, default) for key, (default, converter) in
                      default_meta_des_vars.iteritems() ])

class MetaVars(dict):
    def __setitem__(self, key, val):
        val = MetaVarsAttr(val)
        dict.__setitem__(self, key, val)

class MetaVarsGraph(dict):
    def __setitem__(self, key, val):
        val = MetaVarsAttrGraph(val)
        dict.__setitem__(self, key, val)

class MetaVarsTable(dict):
    def __setitem__(self, key, val):
        val = MetaVarsAttrTable(val)
        dict.__setitem__(self, key, val)

class MetaVarsDes(dict):
    def __setitem__(self, key, val):
        val = MetaVarsAttrDes(val)
        dict.__setitem__(self, key, val)

#
# Now that every type is defined we can populate them with validation
# functions and de fault values, also we can define those defaults and
# validations that involves types defined here.
#
default_meta_graph.update({
    'vars' : [MetaVarsGraph(), MetaVarsGraph],
})

default_meta_table.update({
    'vars' : [MetaVarsTable(), MetaVarsTable],
})

default_meta_des.update({
    'vars' : [MetaVarsDes(), MetaVarsDes],
})

MetaGraph.validate = dict([ (key, converter) for key, (default, converter) in
                                default_meta_graph.iteritems() ])
MetaGraph.defaults = dict([ (key, default) for key, (default, converter) in
                                default_meta_graph.iteritems() ])

MetaTable.validate = dict([ (key, converter) for key, (default, converter) in
                                default_meta_table.iteritems() ])
MetaTable.defaults = dict([ (key, default) for key, (default, converter) in
                                default_meta_table.iteritems() ])

MetaDes.validate = dict([ (key, converter) for key, (default, converter) in
                              default_meta_des.iteritems() ])
MetaDes.defaults = dict([ (key, default) for key, (default, converter) in
                              default_meta_des.iteritems() ])

default_meta.update({
    'table': [MetaTable(), MetaTable],
    'graph': [MetaGraph(), MetaGraph], 
    'des': [MetaDes(), MetaDes], 
    'vars': [MetaVars(), MetaVars]
})

Meta.validate = dict([ (key, converter) for key, (default, converter) in
                           default_meta.iteritems() ])
Meta.defaults = dict([ (key, default) for key, (default, converter) in
                           default_meta.iteritems() ])

