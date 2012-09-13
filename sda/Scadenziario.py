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

lm_registri_iva = {
        'DATE': [0, 'c', 'Data','registrazione'],
        'M_NUM': [1, '0.5c', 'Numero','protocollo'],
        'DATE_DOC': [2, 'c', 'Data ','documento'],
        'M_REF': [3, 'c', 'Numero ','documento '],
        'PARTNER': [4, '1.3c', 'Controparte',"@v3"],
        'T_NAME': [5, '1.5c', 'Tipo','imposta'],
        'BASE': [6, '0.5r', 'Imponibile',"@v1"],
        'TAX': [7, '0.5r', 'Imposta',"@v2"],
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
    comNam=config.options.get('company',False)
    picklesPath = config.options.get('pickles_path',False)
    fiscalyearName=config.options.get('fiscalyear',False)
    #lettura degli oggetti stark di interesse
    companyPathPkl = os.path.join(picklesPath,comNam)
    invoiceStark = Stark.load(os.path.join(companyPathPkl,"INV.pickle"))
    voucherStark = Stark.load(os.path.join(companyPathPkl,"VOU.pickle"))
    periodStark = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    moveLineStark = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
    #calcolo
    expiries = computeExpiries(invoiceStark.DF,voucherStark.DF,periodStark.DF,moveLineStark.DF,fiscalyearName)
    #vatRegister = SDAIva.getVatRegister(vatDf, comNam, onlyValML, fiscalyearName=fiscalyearName, sequenceName=sequenceName)
    #bagVatRegister = Bag(DF=vatRegister,TIP='tab',LM=LMIva.lm_registri_iva)
    #setattr(bagVatRegister,"SEQUENCE",sequenceName)
    #setattr(bagVatRegister,"YEAR",fiscalyearName)
    #setattr(bagVatRegister,"COMPANY_STRING",companyString)
    #OUT_PATH = os.path.join(SRE_PATH, 'registro_iva')
    #bagVatRegister.save(os.path.join(OUT_PATH, 'vat_register.pickle'))
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
    
    invoiceColumns = ["TYPE","DATE_DUE","NUM","STATE","PARTNER","in_invoice","out_invoice"]
    invoiceResultDf = pandas.DataFrame(columns=invoiceColumns)
    
    if fiscalyearDateStart and fiscalyearDateStop:
        ####
        #calcolo fatture in scadenza ancora non pagate
        ####
        invoiceDf['DATE_DUE'].ix[invoiceDf['DATE_DUE'].isnull()] = invoiceDf['DATE_INV']
        df1 = invoiceDf.ix[(invoiceDf["DATE_DUE"]<=fiscalyearDateStop) & (invoiceDf["DATE_DUE"]>=fiscalyearDateStart)]
        df2 = df1.ix[(df1["STATE"]!='paid') & (df1["STATE"]!='cancel')].reset_index()
        df3 = df2[['DATE_DUE','TYPE','NUM','STATE','PARTNER','TOTAL']]
        df3['TOTAL']=df3['TOTAL'].map(float)
        df4 = pandas.pivot_table(df3,values='TOTAL', cols=['TYPE'], 
                        rows=['DATE_DUE','NUM','STATE','PARTNER'])
        df4 = df4.reset_index()
        #formattazione finale
        df4['in_invoice']=df4['in_invoice'].map(str)
        df4['out_invoice']=df4['out_invoice'].map(str)
        df4['in_invoice'].ix[df4['in_invoice']=='nan'] = ''
        df4['STATE'].ix[df4['STATE']=='open'] = 'validata'
        df4['STATE'].ix[df4['STATE']=='draft'] = 'in bozza'
        invoiceDf = df4
        
        ####
        #calcolo liquidazioni in scadenza ancora non pagate
        ####
        voucherDf['DATE_DUE'].ix[voucherDf['DATE_DUE'].isnull()] = voucherDf['DATE']
        df1 = voucherDf.ix[(voucherDf["DATE_DUE"]<=fiscalyearDateStop) & (voucherDf["DATE_DUE"]>=fiscalyearDateStart)]
        df2 = df1.ix[df1["STATE"]!='cancel']
        df3 = df2.ix[(df2["TYPE"]=='sale') | (df2["TYPE"]=='purchase')].reset_index()
        #calcolo delle liquidazioni pagate
        df4 = pandas.merge(df3,moveLineDf,on="NAM_MOV")
        df5 = df4.ix[df4["NAM_REC"].notnull()].reset_index()
        #esclusione delle liquidazioni pagate
        df6 = pandas.DataFrame({'NAM_MOV':list(set(df3['NAM_MOV']) - set(df5['NAM_MOV']))})
        print df6
        #print df5

        #df3 = df2[['DATE_DUE','TYPE','NUM','STATE','PARTNER','TOTAL']]
        #df3['TOTAL']=df3['TOTAL'].map(float)
        #df4 = pandas.pivot_table(df3,values='TOTAL', cols=['TYPE'], 
                        #rows=['DATE_DUE','NUM','STATE','PARTNER'])
        #df4 = df4.reset_index()
        #formattazione finale
        #df4['in_invoice']=df4['in_invoice'].map(str)
        #df4['out_invoice']=df4['out_invoice'].map(str)
        #df4['in_invoice'].ix[df4['in_invoice']=='nan'] = ''
        #df4['STATE'].ix[df4['STATE']=='open'] = 'validata'
        #df4['STATE'].ix[df4['STATE']=='draft'] = 'in bozza'
        #voucherDf = df4
        
    return 0
    
    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))