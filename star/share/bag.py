# -*- coding: utf-8 -*-
import pandas
from star.share.stark import Stark

__all__ = ['Bag']

# stypes are used to determine default action to take when Bag
# instance is part of a report folder.
STYPES = ('grap', 'tab', 'des')

class Bag(Stark):

    def __init__(self, df, md=None, cod=None, stype='tab', 
                 # TODO: remove currency and currdata, as soon UoM are well implemented
                 currency='USD', currdata=None):
        Stark.__init__(self, df, md, cod, stype, currency, currdata)
        # FIXME: keep just tab, different tab flavours are handled via
        # md
        # TODO: handle type cast form Stark to Bag...
        if self.stype in ('tab', 'ltab', 'bodytab'): 
            self._category = 'table'
        elif self.stype == 'graph':
            self._category = 'graph'
        elif self.stype == 'des':
            self._category = 'des'

    @property
    def columns(self):
        return pandas.Index(self._md[self._category]['vars'].keys())

    def plot(self, how='pdf'):
        ''' Wrapper to Graph.out()
        '''
        # TODO: implement method
        raise NotImplementedError
        
    def table(self, how='pdf'):
        ''' Wrapper to Table.out()
        ''' 
        # TODO: implement method
        raise NotImplementedError

    def totals(self, dims):
        ''' Evaluate totals for a dimention. That's like making a
        groupby(dims).sum(). but results are stored in a separate
        DataFrame so further elaborations won't be messed up by those
        values.
        '''
        # TODO: implement method
        raise NotImplementedError

    def set_rows_format(self, modlist):
        # TODO: implement method. 
        # Former set_format(), apply an output format for rows. Old
        # implementation does work, but it may be better to hold
        # modlist in a separate Series and keep it consistent with
        # data by Index.
        raise NotImplementedError

    # def set_format(self, modlist):
    #     ''' Insert line style modifiers in the DF.
        
    #     @ param modlist: a list of tuples (row number, modifier). row numbers
    #         are all referred to the original DF.
    #     Example: [(0, "@b"), (3, "@g")] will insert a blank row as the
    #     beginning and will make the forth row bold.

    #     If a row number is greater than the length of the DataFrame and the
    #     modifier is "@b" or "@i" a new row is added at the end; otherwhise no
    #     action is taken.

    #     If DF has '_OR_' column, its values will be reordered.

    #     '''
    #     # TODO: Why this complexity? Isn't it just:
    #     #     1) Build a df from modlist with modlist[n][0] as index
    #     #     2) join DF with modlistdf on index
    #     #     3) DF[_FR_].fillna('@n')
    #     def cmp_to_key(cmp_or):
    #         'Convert a cmp= function into a key= function'
    #         class K(object):
    #             def __init__(self, obj, *args):
    #                 self.obj = obj
    #             def __lt__(self, other):
    #                 return cmp_or(self.obj, other.obj) < 0
    #             def __gt__(self, other):
    #                 return cmp_or(self.obj, other.obj) > 0
    #             def __eq__(self, other):
    #                 return cmp_or(self.obj, other.obj) == 0
    #             def __le__(self, other):
    #                 return cmp_or(self.obj, other.obj) <= 0
    #             def __ge__(self, other):
    #                 return cmp_or(self.obj, other.obj) >= 0
    #             def __ne__(self, other):
    #                 return cmp_or(self.obj, other.obj) != 0
    #         return K
        
    #     def cmp_modifiers(x, y):
    #         if x[0] != y[0]:
    #             return x[0] - y[0]
    #         else:
    #             a = x[1]
    #             b = y[1]
    #             if a in ("@b", "@i") and not b in ("@b", "@i"):
    #                 return -1
    #             elif not a in ("@b", "@i") and b in ("@b", "@i"):
    #                 return +1
    #             elif (not a in ("@b", "@i") and not b in ("@b", "@i")) or \
    #                     (a in ("@b", "@i") and b in ("@b", "@i")):
    #                 logging.warning(
    #                     "'_OR_' column, check modifiers for row {0}\
    #                      e row {1}".format(x[0], y[0]))
    #                 return 0                    
    #     delta = 0
    #     blank_line = pandas.DataFrame([[""]*len(self.df.columns)],
    #                                   columns=self.df.columns)
    #     new_modlist = list()
    #     # ordiniamo la lista di modifiers per il numero di linea
    #     modlist = [(int(x[0]), x[1]) for x in modlist]
    #     modlist.sort(key=cmp_to_key(cmp_modifiers))
    #     # se è presente la colonna _OR_ considero l'ordine definito in essa
    #     if "_OR_" in self.df.columns:
    #         self.df["_OR_"] = self.df["_OR_"].map(int)
    #         self.df = self.df.sort(["_OR_"])
    #         self.df = self.df.reset_index(True)
    #     for line, modifier in modlist:
    #         line += delta
    #         if line > len(self.df):
    #             line = len(self.df)         
    #         if modifier in ("@b", "@i"):       
    #             self.df = pandas.concat([self.df[:line], 
    #                                      blank_line, 
    #                                      self.df[line:]])
    #             self.df = self.df.reset_index(True)
    #             delta += 1
    #         new_modlist.append((line, modifier))
    #     # setto il valore di default per la colonna _FR_ se non esiste
    #     if "_FR_" not in self.df.columns:
    #         self.df["_FR_"] = "@n"
    #     # aggiungo i modificatori
    #     for line, modifier in new_modlist:
    #         if line >= len(self.df):
    #             continue
    #         self.df["_FR_"][line] = modifier
    #     # aggiorno la colonna _OR_
    #     if "_OR_" in self.df.columns:
    #         self.df["_OR_"] = range(len(self.df))
