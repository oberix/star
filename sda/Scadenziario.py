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
        'out_invoice': [4, '0.5r', 'Entrata',"@v4"],
        'in_invoice': [5, '0.5r', 'Uscita','@v5'],
        }
        
lm_liquidazioni = {
        'DATE_DUE': [0, 'c', 'Data','scadenza'],
        'NUM': [1, 'c', 'Numero','@v1'],
        'STATE': [2, 'c', 'Stato ','@v2'],
        'PARTNER': [3, '2l', 'Controparte',"@v3"],
        'sale': [4, '0.5r', 'Entrata',"@v4"],
        'purchase': [5, '0.5r', 'Uscita','@v5'],
        }


import sys
import os
import getopt
import pandas
import numpy

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

SRE_PATH = os.path.join(BASEPATH,"sre")

from share import Config
from share import Stark
from share import Bag

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
    companyDf = companyStarK.DF
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    #calcolo
    expiries = computeExpiries(invoiceStark.DF,voucherStark.DF,periodStark.DF,moveLineStark.DF,fiscalyearName)
    #generazione e salvataggio bag
    OUT_PATH = os.path.join(SRE_PATH, 'scadenziario')
    bagInvoices = Bag(expiries['invoiceDf'],
                      os.path.join(OUT_PATH, 'invoices.pickle'),
                      TI='tab',LM=lm_fatture,TITLE="Fatture")
    bagVouchers = Bag(expiries['voucherDf'],
                      os.path.join(OUT_PATH, 'vouchers.pickle'),
                      TI='tab',LM=lm_liquidazioni,TITLE="Liquidazioni")
    setattr(bagInvoices,"YEAR",fiscalyearName)
    setattr(bagInvoices,"COMPANY",companyName)
    setattr(bagInvoices,"COMPANY_STRING",companyString)
    bagInvoices.save()
    bagVouchers.save()
    return 0
    
def computeExpiries(invoiceDf , voucherDf , periodDf , moveLineDf, fiscalyearName):
    fiscalyearDateStart = None
    fiscalyearDateStop = None
    df1 = periodDf.ix[periodDf["NAM_FY"]==fiscalyearName]
    df2 = df1[['NAM_FY','FY_DATE_START','FY_DATE_STOP']]
    df2 = df2.drop_duplicates().reset_index()
    if len(df2) > 0:
        fiscalyearDateStart = df2["FY_DATE_START"][0]
        fiscalyearDateStop = df2["FY_DATE_STOP"][0]
    
    invoiceColumns = ["DATE_DUE","NUM","STATE","PARTNER","in_invoice","out_invoice"]
    invoiceResultDf = pandas.DataFrame(columns=invoiceColumns)
    voucherColumns = ["DATE_DUE","NUM","STATE","PARTNER","sale","purchase"]
    voucherResultDf = pandas.DataFrame(columns=voucherColumns)
    
    if fiscalyearDateStart and fiscalyearDateStop:
        ####
        #calcolo fatture in scadenza ancora non pagate
        ####
        invoiceDf['DATE_DUE'].ix[invoiceDf['DATE_DUE'].isnull()] = invoiceDf.ix[invoiceDf['DATE_DUE'].isnull()]['DATE_INV']
        df1 = invoiceDf.ix[(invoiceDf["DATE_DUE"]<=fiscalyearDateStop) & (invoiceDf["DATE_DUE"]>=fiscalyearDateStart)]
        df2 = df1.ix[(df1["STATE"]!='paid') & (df1["STATE"]!='cancel')].reset_index()
        df3 = df2[['DATE_DUE','TYPE','NUM','STATE','PARTNER','TOTAL']]
        df3['TOTAL']=df3['TOTAL'].map(float)
        df4 = pandas.pivot_table(df3,values='TOTAL', cols=['TYPE'], 
                        rows=['DATE_DUE','NUM','STATE','PARTNER'])
        df4 = df4.reset_index()
        #formattazione finale
        columnsList = list(df4.columns)
        if columnsList.count("in_invoice")==0:
            df4["in_invoice"] = ""
        if columnsList.count("out_invoice")==0:
            df4["in_invoice"] = ""
        df4['in_invoice'] = df4['in_invoice'].map(str)
        df4['out_invoice'] = df4['out_invoice'].map(str)
        df4['in_invoice'].ix[df4['in_invoice']=='nan'] = ''
        df4['out_invoice'].ix[df4['out_invoice']=='nan'] = ''
        df4['STATE'].ix[df4['STATE']=='open'] = 'validata'
        df4['STATE'].ix[df4['STATE']=='draft'] = 'in bozza'
        df4 = df4[invoiceColumns]
        invoiceResultDf = df4
        
        ####
        #calcolo liquidazioni in scadenza ancora non pagate
        ####
        voucherDf['DATE_DUE'].ix[voucherDf['DATE_DUE'].isnull()] = voucherDf.ix[voucherDf['DATE_DUE'].isnull()]['DATE']
        df1 = voucherDf.ix[(voucherDf["DATE_DUE"]<=fiscalyearDateStop) & (voucherDf["DATE_DUE"]>=fiscalyearDateStart)]
        df2 = df1.ix[df1["STATE"]!='cancel']
        df3 = df2.ix[(df2["TYPE"]=='sale') | (df2["TYPE"]=='purchase')].reset_index(drop=True)
        #calcolo delle liquidazioni pagate
        df4 = pandas.merge(df3,moveLineDf,on="NAM_MOV")
        df5 = df4.ix[df4["ID_REC"].notnull()].reset_index()
        #esclusione delle liquidazioni pagate
        df6 = pandas.DataFrame({'NAM_MOV':list(set(df3['NAM_MOV']) - set(df5['NAM_MOV']))})
        df7 = pandas.merge(df3,df6,on="NAM_MOV")
        df7['AMOUNT']=df7['AMOUNT'].map(float)
        if len(df7) > 0:
            df8 = pandas.pivot_table(df7,values='AMOUNT', cols=['TYPE'], 
                            rows=['DATE_DUE','NUM','STATE','PARTNER'])
            df8 = df8.reset_index()
            #formattazione finale
            columnsList = list(df8.columns)
            if columnsList.count("purchase")==0:
                df8["purchase"] = ""
            if columnsList.count("sale")==0:
                df8["sale"] = ""
            df8['purchase'] = df8['purchase'].map(str)
            df8['sale'] = df8['sale'].map(str)
            df8['purchase'].ix[df8['purchase']=='nan'] = ''
            df8['sale'].ix[df8['sale']=='nan'] = ''
            df8['STATE'].ix[df8['STATE']=='posted'] = 'validata'
            df8['STATE'].ix[df8['STATE']=='draft'] = 'in bozza'
            df8 = df8[voucherColumns]
            voucherResultDf = df8
    
    return {
        'invoiceDf' : invoiceResultDf,
        'voucherDf' : voucherResultDf,
        }
    
    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
