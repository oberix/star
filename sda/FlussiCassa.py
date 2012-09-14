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
        'PARTNER': [3, '2c', 'Controparte',"@v3"],
        'out_invoice': [4, '0.5r', 'Entrata',"@v4"],
        'in_invoice': [5, '0.5c', 'Uscita','@v5'],
        }
        
lm_liquidazioni = {
        'DATE_DUE': [0, 'c', 'Data','scadenza'],
        'NUM': [1, 'c', 'Numero','@v1'],
        'STATE': [2, 'c', 'Stato ','@v2'],
        'PARTNER': [3, '2c', 'Controparte',"@v3"],
        'sale': [4, '0.5r', 'Entrata',"@v4"],
        'purchase': [5, '0.5c', 'Uscita','@v5'],
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
    configFilePath = os.path.join(BASEPATH,"config","flussi_cassa.cfg")
    config = Config(configFilePath)
    config.parse()
    #assegna ai parametri di interesse il valore letto in config
    companyName = config.options.get('company',False)
    picklesPath = config.options.get('pickles_path',False)
    fiscalyearName=config.options.get('fiscalyear',False)
    defaultIncomingsFlowLineCode = config.options.get('default_incomings_flow_line',False)
    defaultExpensesFlowLineCode = config.options.get('default_expenses_flow_line',False)
    totalIncomingsFlowLineCode = config.options.get('total_incomings_flow_line',False)
    totalExpensesFlowLineCode = config.options.get('total_expenses_flow_line',False)
    linesCsvFilePath = config.options.get('lines_csv_file_path',False)
    matchingsCsvFilePath = config.options.get('matchings_csv_file_path',False)
    incomingAccountsCsvFilePath = config.options.get('incoming_accounts_csv_file_path',False)
    costAccountsCsvFilePath = config.options.get('cost_accounts_csv_file_path',False)
    #lettura degli oggetti stark di interesse
    companyPathPkl = os.path.join(picklesPath,companyName)
    accountStark = Stark.load(os.path.join(companyPathPkl,"ACC.pickle"))
    periodStark = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    moveLineStark = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
    companyStarK = Stark.load(os.path.join(companyPathPkl,"COMP.pickle"))
    companyDf = companyStarK.DF
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    #lettura csv
    linesDf = pandas.read_csv(linesCsvFilePath, sep=";", header=0)
    matchingsDf = pandas.read_csv(matchingsCsvFilePath, sep=";", header=0)
    incomingsDf = pandas.read_csv(incomingAccountsCsvFilePath, sep=";", header=0)
    costsDf = pandas.read_csv(costAccountsCsvFilePath, sep=";", header=0)
    #controllo conti
    checkAccounts(matchingsDf,accountStark.DF)
    #calcolo entrate e uscite
    
    #calcolo
    #expiries = computeExpiries(invoiceStark.DF,voucherStark.DF,periodStark.DF,moveLineStark.DF,fiscalyearName)
    #generazione e salvataggio bag
    #bagInvoices = Bag(DF=expiries['invoiceDf'],TIP='tab',LM=lm_fatture,TITLE="Fatture")
    #bagVouchers = Bag(DF=expiries['voucherDf'],TIP='tab',LM=lm_liquidazioni,TITLE="Liquidazioni")
    #setattr(bagInvoices,"YEAR",fiscalyearName)
    #setattr(bagInvoices,"COMPANY",companyName)
    #setattr(bagInvoices,"COMPANY_STRING",companyString)
    #OUT_PATH = os.path.join(SRE_PATH, 'scadenziario')
    #bagInvoices.save(os.path.join(OUT_PATH, 'invoices.pickle'))
    #bagVouchers.save(os.path.join(OUT_PATH, 'vouchers.pickle'))
    return 0

###########
## funzioni di calcolo
###########

def checkAccounts(matchingsDf, accountsDf):
    df1 = matchingsDf[["servabit_code"]]
    df2 = accountsDf[(accountsDf["TYP_CON"]=="other") | (accountsDf["TYP_CON"]=="receivable") |\
                    (accountsDf["TYP_CON"]=="payable")  | (accountsDf["TYP_CON"]=="liquidity")].reset_index(drop=True)
    df2 = df2[["COD_CON"]]
    df3 = pandas.merge(df1,df2,left_on="servabit_code",right_on="COD_CON",how="outer")
    df4 = df3[(df3["COD_CON"].isnull())].reset_index(drop=True)
    for i in range(len(df4)):
        row = df4[i:i+1]
        code = row['servabit_code'][i]
        print "Warning: il conto "+code.encode('utf8')+" è presente nel file csv delle corrispondenze ma non è presente nel db"
    df5 = df3[(df3["servabit_code"].isnull())].reset_index(drop=True)
    for i in range(len(df5)):
        row = df5[i:i+1]
        code = row['COD_CON'][i]
        print "Warning: il conto "+code.encode('utf8')+" è presente nel db ma non nel file csv delle corrispondenze"
        
def computeIncomingAndCosts(session, fiscalyearName, incomingsDf, costsDf, onlyValidatedMoves=True):
    

    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))