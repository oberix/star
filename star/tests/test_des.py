# -*- coding: utf-8 -*-

import os
import sys
import logging
import random as rnd
import pandas as pnd
from operator import itemgetter as ig

# star_path = path della directroy principale
star_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         os.path.pardir,
                                         os.path.pardir))
if star_path in sys.path:
    # rimuoviamo tutte le occorrenze di star_path
    sys.path = [p for p in sys.path if p != star_path]
# inseriamo star_path in seconda posizione, la prima dovrebbe essere riservata
# alla cartella corrente in cui è poisizionato il file
sys.path.insert(1, star_path)
from star.remida.des import TexDes
import star.share.bag as bag


def main():
    logging.basicConfig(level=logging.INFO)
    
    # quadro macroeconomico
    cod = ""
    aree = ["AreaPIndustr", "AreaPTransizione", "AreaPSviluppo"]
    nome = "pàèsè {0}".format(rnd.randrange(0, 100))
    area = aree[rnd.randrange(3)]
    info = {"ISO3": nome, "nome": nome, "area": area}
    cagrPIL = dict(("pàèsè {0}".format(i), rnd.uniform(-20, 20)) for i in
                   xrange(100))
    cagrPIL["AreaPIndustr"] = rnd.uniform(-20, 20)
    cagrPIL["AreaPTransizione"] = rnd.uniform(-20, 20)
    cagrPIL["AreaPSviluppo"] = rnd.uniform(-20, 20)
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
    bp = rnd.uniform(-50, 50)
    idx_lavoro = (rnd.uniform(0, 200), rnd.uniform(0, 200))
    df = pnd.DataFrame([[info, cagrPIL, sc, var, bp, idx_lavoro]],
                       columns=["paese", "cagr", "sc", "var", "bil", "idx"])
      
    lm = {"paese": "paese", "cagr": "cagr", "sc": "saldo commerciale",
          "var": "variazione saldo", "bil": "bilancia pagamenti",
          "idx": "indice relativo costo lavoro"}
      
    b = bag.Bag(df, cod=cod, stype="desc", lm=lm)
    with open(os.path.join("/home/lcurzi/testi_auto/"
                           "main_quadro_macroeconomico.xml"), "rb") as fd:
        main_file = fd.read()
      
    with open(os.path.join("/home/lcurzi/testi_auto/"
                           "portfolio_quadro_macroeconomico.xml"), "rb") as fd:
        portfolio_file = fd.read()
      
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
    list_pos.append({"nome": "totale", "saldo": sum([s["saldo"] for s in
                                                     list_pos])})
    list_neg = [{"nome": "merceologià {0}".format(20 + i),
                 "saldo": rnd.uniform(-10000, 0)}
                for i in xrange(20)]
    list_neg.sort(key=ig("saldo"))
    list_neg.append({"nome": "totale", "saldo": sum([s["saldo"] for s in
                                                     list_neg])})
      
    df = pnd.DataFrame({"lpos": [list_pos], "lneg": [list_neg]})
      
    lm = {"lpos": "lista merceologie positive",
          "lneg": "lista merceologie negative"}
      
    b = bag.Bag(df, cod=cod, stype="desc", lm=lm)
    with open(os.path.join("/home/lcurzi/main_flussi.xml"), "rb") as fd:
        main_file = fd.read()
      
    with open(os.path.join("/home/lcurzi/portfolio_flussi.xml"), "rb") as fd:
        portfolio_file = fd.read()
      
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
    list_pos.append({"nome": "totale",
                     "saldo": sum([s["saldo"] for s in list_pos])})
    list_pos = []
    list_neg = [{"nome": "categoria {0}".format(20 + i),
                 "saldo": rnd.uniform(-10000, 0)}
                for i in xrange(20)]
    list_neg.sort(key=ig("saldo"))
    list_neg.append({"nome": "totale", "saldo": sum([s["saldo"] for s in
                                                     list_neg])})
      
    df = pnd.DataFrame({"lpos": [list_pos], "lneg": [list_neg]})
      
    lm = {"lpos": "lista categorie positive",
          "lneg": "lista categorie negative"}
      
    b = bag.Bag(df, cod=cod, stype="desc", lm=lm)
    with open(os.path.join("/home/lcurzi/main_categorie.xml"), "rb") as fd:
        main_file = fd.read()
      
    with open(os.path.join("/home/lcurzi/portfolio_categorie.xml"),
              "rb") as fd:
        portfolio_file = fd.read()
      
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
