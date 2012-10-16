#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################


#################
######definizione degli lm
#################

lm_fatture = {
        'DATE_DUE': [0, 'c', 'Data','scadenza'],
        'NUM': [1, 'c', 'Numero','@v1'],
        'STATE': [2, 'c', 'Stato ','@v2'],
        'PARTNER': [3, '2l', 'Controparte',"@v3"],
        'TOTAL': [4, '0.5r', 'Importo',"@v4"],
        }
        
lm_liquidazioni = {
        'DATE_DUE': [0, 'c', 'Data','scadenza'],
        'NUM': [1, 'c', 'Numero','@v1'],
        'STATE': [2, 'c', 'Stato ','@v2'],
        'PARTNER': [3, '2l', 'Controparte',"@v3"],
        'AMOUNT': [4, '0.5r', 'Importo',"@v4"],
        }


import sys
import os
import getopt
import ScadenziarioLib

import sda
from share import Config
from share import Stark
from share import Bag

SRE_PATH = os.path.join(BASEPATH,"sre")


def main(dirname):
    #legge il file config    
    configFilePath = os.path.join(BASEPATH,"config","scadenziario.cfg")
    config = Config(configFilePath)
    config.parse()
    #assegna ai parametri di interesse il valore letto in config
    companyName = config.options.get('company',False)
    picklesPath = config.options.get('pickles_path',False)
    fiscalyearName=config.options.get('fiscalyear',False)
    #lettura degli oggetti stark di interesse
    companyPathPkl = os.path.join(picklesPath,companyName)
    invoiceStark = Stark.load(os.path.join(companyPathPkl,"INV.pickle"))
    voucherStark = Stark.load(os.path.join(companyPathPkl,"VOU.pickle"))
    periodStark = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    moveLineStark = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
    companyStarK = Stark.load(os.path.join(companyPathPkl,"COMP.pickle"))
    companyDf = companyStarK.df
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    #calcolo
    expiries = ScadenziarioLib.computeExpiries(invoiceStark.df,voucherStark.df,periodStark.df,moveLineStark.df,fiscalyearName)
    #generazione e salvataggio bag
    OUT_PATH = os.path.join(SRE_PATH, 'scadenziario')
    inInvoicesBag = Bag(expiries['inInvoiceDf'],
                      os.path.join(OUT_PATH, 'in_invoices.pickle'),
                      bag_type='tab',meta=lm_fatture,title="Fatture acquisto")
    outInvoicesBag = Bag(expiries['outInvoiceDf'],
                      os.path.join(OUT_PATH, 'out_invoices.pickle'),
                      bag_type='tab',meta=lm_fatture,title="Fatture vendita")
    purchaseVoucherBag = Bag(expiries['purchaseVoucherDf'],
                      os.path.join(OUT_PATH, 'purchase_vouchers.pickle'),
                      bag_type='tab',meta=lm_liquidazioni,title="Liquidazioni costo")
    setattr(inInvoicesBag,"YEAR",fiscalyearName)
    setattr(inInvoicesBag,"COMPANY",companyName)
    setattr(inInvoicesBag,"COMPANY_STRING",companyString)
    inInvoicesBag.save()
    outInvoicesBag.save()
    purchaseVoucherBag.save()
    return 0
    
    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
