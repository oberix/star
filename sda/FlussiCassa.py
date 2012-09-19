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
import calendar
from datetime import date

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
    #incomingAccountsCsvFilePath = config.options.get('incoming_accounts_csv_file_path',False)
    #costAccountsCsvFilePath = config.options.get('cost_accounts_csv_file_path',False)
    #verifica che la stringa associata al parametro only_validated_moves inserita in config
    #sia effettivamente un valore boleano 
    onlyValidatedMoves = True
    if str(config.options.get('only_validated_moves',True))=='False':
        onlyValidatedMoves = False
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
    #incomingsDf = pandas.read_csv(incomingAccountsCsvFilePath, sep=";", header=0)
    #costsDf = pandas.read_csv(costAccountsCsvFilePath, sep=";", header=0)
    #controllo conti
    checkAccounts(matchingsDf,accountStark.DF)
    #calcolo flussi
    computeCashFlows(fiscalyearName,moveLineStark.DF,accountStark.DF,
                    periodStark.DF,matchingsDf,onlyValidatedMoves,
                    defaultIncomingsFlowLineCode,defaultExpensesFlowLineCode,
                    printWarnings=True)
    #calcolo
    #expiries = computeExpiries(invoiceStark.DF,voucherStark.DF,periodStark.DF,moveLineStark.DF,fiscalyearName)
    #generazione e salvataggio bag
    #bagInvoices = Bag(expiries['invoiceDf'], os.path.join(OUT_PATH, 'invoices.pickle'), TI='tab',LM=lm_fatture,TITLE="Fatture")
    #bagVouchers = Bag(expiries['voucherDf'], os.path.join(OUT_PATH, 'vouchers.pickle'), TI='tab',LM=lm_liquidazioni,TITLE="Liquidazioni")
    #setattr(bagInvoices,"YEAR",fiscalyearName)
    #setattr(bagInvoices,"COMPANY",companyName)
    #setattr(bagInvoices,"COMPANY_STRING",companyString)
    #OUT_PATH = os.path.join(SRE_PATH, 'scadenziario')
    #bagInvoices.save()
    #bagVouchers.save()
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
        
def computeCashFlows(fiscalyearName, moveLineDf, accountDf, periodDf,
                    matchingsDf, onlyValidatedMoves, defaultIncomingsFlowLineCode,
                    defaultExpensesFlowLineCode, printWarnings=True):
    #recupero conti di liquidità
    liquidityAccountsDf = accountDf[accountDf["TYP_CON"]=='liquidity'].reset_index(drop=True)
    #calcolo intero relativo all'anno fiscale
    df0 = periodDf[periodDf["NAM_FY"]==fiscalyearName]
    df1 = df0[["FY_DATE_START"]].drop_duplicates().reset_index()
    year = (df1["FY_DATE_START"][0]).year
    #costruzione df per i risultati
    incomingCodesDf = matchingsDf[["entrata_code"]].drop_duplicates().reset_index(drop=True)
    incomingCodesList = list(incomingCodesDf["entrata_code"])
    exitCodesDf = matchingsDf[["uscita_code"]].drop_duplicates().reset_index(drop=True)
    exitCodesList = list(exitCodesDf["uscita_code"])
    incomingCodesList.extend(exitCodesList)
    cashFlowsDf = pandas.DataFrame(columns=incomingCodesList)
    #calcolo dei risultati per ogni mese
    if onlyValidatedMoves:
        moveLineDf = moveLineDf[moveLineDf["STA_MOV"]=='posted'].reset_index(drop=True)
    for month in range(12):
        month += 1
        if printWarnings:
            print month
        lastDay = calendar.monthrange(year,month)[1]
        dateStart = date(year,month,1)
        dateEnd = date(year,month,lastDay)
        df0 = liquidityAccountsDf[["COD_CON"]]
        df1 = pandas.merge(moveLineDf,df0,on="COD_CON")
        df2 = df1[(df1["DAT_MVL"]>=dateStart) & (df1["DAT_MVL"]<=dateEnd)].reset_index(drop=True)
        df2['DBT_MVL'] = df2['DBT_MVL'].map(float)
        df2['CRT_MVL'] = df2['CRT_MVL'].map(float)
        if len(df2) > 0:
            #calcolo flussi per journal
            df3 = df2.groupby("NAM_JRN").sum()[['DBT_MVL','CRT_MVL']].reset_index()
           
            #funzione interna utilizzata solo in questo contesto
            def computeCashFlowFromReconcile(cashFlowsDf, defaultFlowLine, reconcilesDf, moveLineDf, amountInCredit):
                '''
                @param amountInCredit: è un boolean. se True -> amount = credit - debit , se False -> viceversa
                '''
                reconcilesDf = reconcilesDf[["ID_MVL","DBT_REC","CRT_REC","NAM_MOV","NAM_FY","NAM_JRN","percentage"]]
                df1 = moveLineDf.rename(columns={'CRT_MVL' : 'CRT_INV', 'DBT_MVL' : 'DBT_INV'})
                df2 = pandas.merge(reconcilesDf,df1,on=["NAM_MOV","NAM_FY","NAM_JRN"])
                df2 = df2[df2["ID_MVL"]!=df2["ID0_MVL"]].reset_index(drop=True)
                if amountInCredit:
                    df2["AMOUNT"] = df2["CRT_INV"]-df2["DBT_INV"]
                    df2["REC_AMOUNT"] = df2["DBT_REC"]-df2["CRT_REC"]
                else:
                    df2["AMOUNT"] = df2["DBT_INV"]-df2["CRT_INV"]
                    df2["REC_AMOUNT"] = df2["CRT_REC"]-df2["DBT_REC"]
                #calcolo errori nelle scritture contabili
                df3 = df2[df2["AMOUNT"]>df2["REC_AMOUNT"]].reset_index(drop=True)
                if len(df3)>0 and printWarnings:
                    print "Errore a: le seguenti move line hanno importo maggiore della move.line riconciliata. Verranno scartate dai flussi di cassa"
                    print df3[["ID0_MVL","DAT_MVL","NAM_MOV","NAM_MVL"]]
                #calcolo flussi
                df4 = df2[df2["AMOUNT"]<=df2["REC_AMOUNT"]].reset_index(drop=True)
                df4["AMOUNT"] = df4["AMOUNT"] * df4["percentage"]
                df5 = pandas.merge(df4,matchingsDf,left_on="COD_CON",right_on="servabit_code")
                df6 = None
                if amountInCredit:
                    df6 = df5[["entrata_code","AMOUNT"]]
                    df6 = df6.rename(columns={'entrata_code' : 'code'})
                else:
                    df6 = df5[["uscita_code","AMOUNT"]]
                    df6 = df6.rename(columns={'uscita_code' : 'code'})
                df7 = df6.groupby("code").sum()[['AMOUNT']].reset_index()
                for i in range(len(df7)):
                    row = df7[i:i+1]
                    code = row["code"][i]
                    amount = row["AMOUNT"][i]
                    cashFlowsDf[code] += amount

                print cashFlowsDf
            
            #calcolo flussi suddivisi in voci
            df4 = df2[["NAM_MOV","NAM_FY","NAM_JRN"]]
            if len(df4) > 0:
                df5 = pandas.merge(moveLineDf,df4,on=["NAM_MOV","NAM_FY","NAM_JRN"])
                df6 = df5[df5["TYP_CON"]!='liquidity'].reset_index(drop=True)
                #flussi per conti 'payable'
                df7 = df6[df6["TYP_CON"]=='payable'].reset_index(drop=True)
                df8 = df7[df7["ID_REC"].notnull()]
                df8 = df8.rename(columns={'CRT_MVL' : 'CRT_PAYED', 'DBT_MVL' : 'DBT_PAYED'})
                df8 = df8[["CRT_PAYED","DBT_PAYED","ID_REC","ID0_MVL"]]
                df15 = moveLineDf.rename(columns={'CRT_MVL' : 'CRT_REC', 'DBT_MVL' : 'DBT_REC'})
                df9 = pandas.merge(df15,df8,on="ID_REC")
                df9 = df9[df9["ID0_MVL.x"]!=df9["ID0_MVL.y"]].reset_index(drop=True)
                del df9["ID0_MVL.y"]
                df9 = df9.rename(columns={'ID0_MVL.x' : 'ID_MVL'})
                df10 = df9[df9["CRT_REC"]>0].reset_index(drop=True)
                df11 = df9[(df9["CRT_REC"]==0) & (df9["DBT_REC"]==df9["CRT_PAYED"])].reset_index(drop=True)
                if len(df11)>0 and printWarnings:
                    print "Errore c: le seguenti move line hanno importo di dare >0."+\
                            "Verranno scartata dai flussi di cassa in quanto non possono rifersi ad un pagamento su un conto payable"
                    print df11[["ID_MVL","DAT_MVL","NAM_MOV"]]
                if len(df10)>0:
                    #compute reconcile percentage
                    df10["percentage"] = df10["DBT_PAYED"]/df10["CRT_REC"]
                    df10['percentage'] = numpy.where(df10['percentage']>1,1,df10['percentage'])
                    computeCashFlowFromReconcile(cashFlowsDf,defaultExpensesFlowLineCode,df10,moveLineDf,False)
                
    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
