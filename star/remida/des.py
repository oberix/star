# -*- coding: utf-8 -*-

################################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Luigi Curzi <tremst@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 2 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

import os
import sys
import logging
import traceback as trb
import des_engines as de
import utils as ut
logging.basicConfig(level=logging.INFO)

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(sys.argv[0]),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))


class Des(object):
    '''
    classe per l'oggetto testo automatico
    '''
    def __init__(self, data):
        try:
            engine_name = data.engine.lower()
        except:
            # FIXME: raise a warning
            logging.debug(u"{0}".format(trb.format_exc()))
            engine_name = "xml"
        
        main_string = unicode(data.main, "utf8")
        try:
            portfolio_string = unicode(data.portfolio, "utf8")
        except:
            # FIXME: raise a warning
            logging.debug(u"{0}".format(trb.format_exc()))
            portfolio_string = ""
        
        try:
            self.df = data.df.rename(columns=data.lm)
        except:
            # FIXME: raise a warning
            logging.debug(u"{0}".format(trb.format_exc()))
            self.df = None    
        
        engine_class = getattr(de, "{0}_engine".format(engine_name))
        self.engine = engine_class(main_string, portfolio_string, self.df)
        self.tree = self.engine.get_tree()
    
    def out(self):
        raise NotImplementedError
    

class TexDes(Des):
    def __init__(self, data):
        Des.__init__(self, data)
        
    def out(self):
        res = self.tree.to_string()
        res = ut.escape(res, ut.TEX_ESCAPE)
        res = " ".join(res.split())
        res = res.replace(" .", ".")
        res = res.replace(" ,", ",")
        res = res.replace(" ;", ";")
        res = res.replace(" :", ":")
        res = unicode("{{{0}}}", "utf8").format(res)
        return res
    

class HTMLDes(Des):
    def __init__(self, data):
        Des.__init__(self, data)           
    
    def out(self):
        res = []
        for paragraph in self.paragraphs:
            paragraph_id = paragraph["id"]
            paragraph_text = self.elab_text(paragraph["value"])
            res.append(unicode("<div id='{0}' class='paragraph'>", 
                               "utf8").format(paragraph_id))
            res.append(paragraph_text)
            res.append(unicode("</div>", "utf8"))
        return unicode("", "utf8").join(res)
    

def main():
    import random as rnd
    import pandas as pnd
    import star.share.bag as bag
    from operator import itemgetter as ig
    logging.basicConfig(level=logging.DEBUG)
    
    # quadro macroeconomico
    cod = ""
    
    aree = ["AreaPIndustr", "AreaPTransizione", "AreaPSviluppo"]
    nome = "pàèsè {0}".format(rnd.randrange(0, 100))
    area = aree[rnd.randrange(3)]
    info = {"ISO3": nome, "nome": nome, "area": area}
    cagrPIL = dict(("pàèsè {0}".format(i), rnd.uniform(-20,20)) for i in xrange(100))
    cagrPIL["AreaPIndustr"] = rnd.uniform(-20,20)
    cagrPIL["AreaPTransizione"] = rnd.uniform(-20,20)
    cagrPIL["AreaPSviluppo"] = rnd.uniform(-20,20)
    exp = rnd.uniform(1, 5000)
    imp = rnd.uniform(1, 5000)
    exp0 = rnd.uniform(1, 5000)
    imp0 = rnd.uniform(1, 5000)
    sc = exp - imp
    sc0 = exp0 - imp0
    vsc = (sc / sc0) * 100 - 100
    vexp = (exp / exp0) * 100 - 100
    vimp = (imp / imp0) * 100 - 100
    var = {"vexp": vexp, "vimp": vimp, "vsc": vsc}
    bp = rnd.uniform(-50,50)
    idx_lavoro = (rnd.uniform(0,200), rnd.uniform(0,200))
    df = pnd.DataFrame([[info, cagrPIL, sc, var, bp, idx_lavoro]],
                       columns=["paese", "cagr", "sc", "var", "bil", "idx"])
    
    lm = {"paese": "paese", "cagr": "cagr", "sc": "saldo commerciale", 
          "var": "variazione saldo", "bil": "bilancia pagamenti", 
          "idx": "indice relativo costo lavoro"}
    
    b = bag.Bag(df, cod=cod, stype="desc", lm=lm)
    with open(os.path.join("/home/lcurzi/main_quadro_macroeconomico.xml"), "rb") as fd:
        main_file =  fd.read()
    
    with open(os.path.join("/home/lcurzi/portfolio_quadro_macroeconomico.xml"), "rb") as fd:
        portfolio_file =  fd.read()    
    
    b.main = main_file
    b.portfolio = portfolio_file
    b.engine = "xml"
    
    print("----------")
    logging.info(u"dataframe: {0}".format(b.df.T))
    print("\n")
    
    td = TexDes(b)
    o = td.out()
    
    print("----------")
    logging.info(u"output: {0}".format(o))
    print("\n")
    print("\n")
    
    # flussi
    cod = ""
        
    list_pos = [{"nome": "merceologià {0}".format(i), 
                 "saldo": rnd.uniform(0, +10000)} 
                for i in xrange(20)]
    list_pos.sort(reverse=True, key=ig("saldo"))
    list_pos.append({"nome": "totale", "saldo": sum([s["saldo"] for s in list_pos])})
    list_neg = [{"nome": "merceologià {0}".format(20 + i), 
                 "saldo": rnd.uniform(-10000, 0)} 
                for i in xrange(20)]
    list_neg.sort(key=ig("saldo"))
    list_neg.append({"nome": "totale", "saldo": sum([s["saldo"] for s in list_neg])})
    
    df = pnd.DataFrame({"lpos": [list_pos], "lneg": [list_neg]})
    
    lm = {"lpos": "lista merceologie positive", 
          "lneg": "lista merceologie negative",}
    
    b = bag.Bag(df, cod=cod, stype="desc", lm=lm)
    with open(os.path.join("/home/lcurzi/main_flussi.xml"), "rb") as fd:
        main_file =  fd.read()
    
    with open(os.path.join("/home/lcurzi/portfolio_flussi.xml"), "rb") as fd:
        portfolio_file =  fd.read()    
    
    b.main = main_file
    b.portfolio = portfolio_file
    b.engine = "xml"
    
    print("----------")
    logging.info(u"lpos:")
    for e in list_pos:
        logging.info(u"{0}".format(e))
    print("\n")
    logging.info(u"lneg:")
    for e in list_neg:
        logging.info(u"{0}".format(e))
    print("\n")
    
    td = TexDes(b)
    o = td.out()
    
    print("----------")
    logging.info(u"output: {0}".format(o))
    print("\n")
    print("\n")
    
    # categorie
    cod = ""
        
    list_pos = [{"nome": "categoria {0}".format(i), 
                 "saldo": rnd.uniform(0, +10000)} 
                for i in xrange(20)]
    list_pos.sort(reverse=True, key=ig("saldo"))
#    list_pos.append({"nome": "totale", 
#                     "saldo": sum([s["saldo"] for s in list_pos])})
    list_neg = [{"nome": "categoria {0}".format(20 + i), 
                 "saldo": rnd.uniform(-10000, 0)} 
                for i in xrange(20)]
    list_neg.sort(key=ig("saldo"))
    list_neg.append({"nome": "totale", "saldo": sum([s["saldo"] for s in list_neg])})
    
    df = pnd.DataFrame({"lpos": [list_pos], "lneg": [list_neg]})
    
    lm = {"lpos": "lista categorie positive", 
          "lneg": "lista categorie negative",}
    
    b = bag.Bag(df, cod=cod, stype="desc", lm=lm)
    with open(os.path.join("/home/lcurzi/main_categorie.xml"), "rb") as fd:
        main_file =  fd.read()
    
    with open(os.path.join("/home/lcurzi/portfolio_categorie.xml"), "rb") as fd:
        portfolio_file =  fd.read()    
    
    b.main = main_file
    b.portfolio = portfolio_file
    b.engine = "xml"
    
    print("----------")
    logging.info(u"lpos:")
    for e in list_pos:
        logging.info(u"{0}".format(e))
    print("\n")
    logging.info(u"lneg:")
    for e in list_neg:
        logging.info(u"{0}".format(e))
    print("\n")
    
    td = TexDes(b)
    o = td.out()
    
    print("----------")
    logging.info(u"output: {0}".format(o))
    print("\n")
    
if __name__ == '__main__':
    main()
