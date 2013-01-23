# -*- coding: utf-8 -*-
from star.share import utils
from star.share.default_meta import default_meta, default_meta_vars,\
    default_meta_graph, default_meta_graph_vars, default_meta_table,\
    default_meta_table_vars, default_meta_des, default_meta_des_vars

'''
This is the objects composition hierarchy:

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
See %s.defaults for a list of valid parameters." % (key, self.__class__.__name__))
        dict.__setitem__(self, key, cval)

    def __getattribute__(self, name):
        try:
            return super(Meta, self).__getattribute__(name)
        except AttributeError, err:
            try:
                return self.__getitem__(name)
            except KeyError:
                raise err

    def __setattr__(self, name, value):
        self.__setitem__(name, value)

    def __delattr__(self, name):
        # alias to __delitem__()
        self.__delitem__(name)

    def __delitem__(self, name):
        # items can not be deleted, just fallback to default value
        self.__setitem__(name, self.defaults[name])

    def copy(self):
        return utils.smartcopy(self)

# Dummy definitions to populate namespace, more below...
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

#
# The following classes are a little different because theirs keys can not be
# validated since they are named after the DataFrame columns. Maybe
# Stak could do this kind of checking, but it's limiting at this stage
#
class MetaVars(Meta):
    
    _sublevel = MetaVarsAttr

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    
    def new(self, varname):
        self.__setitem__(varname, type(self)._sublevel())

    def __setitem__(self, key, val):
        val = type(self)._sublevel(val)
        dict.__setitem__(self, key, val)

    def __delitem__(self, name):
        # Elements at this level are custom, so deletion is allowed
        dict.__delitem__(self, name)

class MetaVarsGraph(MetaVars):
    _sublevel = MetaVarsAttrGraph

class MetaVarsTable(MetaVars):
    _sublevel = MetaVarsAttrTable

class MetaVarsDes(MetaVars):
    _sublevel = MetaVarsAttrDes

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

