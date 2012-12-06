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
import pandas
import numpy


def computeExpiries(invoiceDf , voucherDf , periodDf , moveLineDf, fiscalyearName):
    fiscalyearDateStart = None
    fiscalyearDateStop = None
    df1 = periodDf.ix[periodDf["NAM_FY"]==fiscalyearName]
    df2 = df1[['NAM_FY','FY_DATE_START','FY_DATE_STOP']]
    df2 = df2.drop_duplicates().reset_index()
    if len(df2) > 0:
        fiscalyearDateStart = df2["FY_DATE_START"][0]
        fiscalyearDateStop = df2["FY_DATE_STOP"][0]
    
    invoiceColumns = ["DATE_DUE","NUM","STATE","PARTNER","TOTAL"]
    inInvoiceResultDf = pandas.DataFrame(columns=invoiceColumns)
    outInvoiceResultDf = pandas.DataFrame(columns=invoiceColumns)
    voucherColumns = ["DATE_DUE","NUM","STATE","PARTNER","AMOUNT"]
    saleVoucherResultDf = pandas.DataFrame(columns=voucherColumns)
    purchaseVoucherResultDf = pandas.DataFrame(columns=voucherColumns)
    
    if fiscalyearDateStart and fiscalyearDateStop:
        ####
        #calcolo fatture in scadenza ancora non pagate
        ####
        invoiceDf['DATE_DUE'].ix[invoiceDf['DATE_DUE'].isnull()] = invoiceDf.ix[invoiceDf['DATE_DUE'].isnull()]['DATE_INV']
        df1 = invoiceDf.ix[(invoiceDf["DATE_DUE"]<=fiscalyearDateStop) & (invoiceDf["DATE_DUE"]>=fiscalyearDateStart)]
        df2 = df1.ix[(df1["STATE"]!='paid') & (df1["STATE"]!='cancel')].reset_index()
        if len(df2) > 0:
            df3 = df2[['DATE_DUE','TYPE','NUM','STATE','PARTNER','TOTAL']]
            df3['STATE'].ix[df3['STATE']=='open'] = 'validata'
            df3['STATE'].ix[df3['STATE']=='draft'] = 'in bozza'
            inInvoiceResultDf = df3[df3["TYPE"]=='in_invoice']
            inInvoiceResultDf = inInvoiceResultDf[invoiceColumns]
            outInvoiceResultDf = df3[df3["TYPE"]=='out_invoice']
            outInvoiceResultDf = outInvoiceResultDf[invoiceColumns]
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
        if len(df7) > 0:
            df7['STATE'].ix[df7['STATE']=='posted'] = 'validata'
            df7['STATE'].ix[df7['STATE']=='draft'] = 'in bozza'
            saleVoucherResultDf = df7[dft["TYPE"]=='sale']
            saleVoucherResultDf = saleVoucherResultDf[voucherColumns]
            purchaseVoucherResultDf = df7[dft["TYPE"]=='purchase']
            purchaseVoucherResultDf = purchaseVoucherResultDf[voucherColumns]
    
    return {
        'inInvoiceDf' : inInvoiceResultDf,
        'outInvoiceDf' : outInvoiceResultDf,
        'purchaseVoucherDf' : purchaseVoucherResultDf,
        }