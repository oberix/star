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

lm_flussi = {
        'descrizione': [0, '3l', '@v10'],
        1: [1, 'r', 'gen'],
        2: [2, 'r', 'feb'],
        3: [3, 'r', 'mar'],
        4: [4, 'r', 'apr'],
        5: [5, 'r', 'mag'],
        6: [6, 'r', 'giu'],
        7: [7, 'r', 'lug'],
        8: [8, 'r', 'ago'],
        9: [9, 'r', 'set'],
        10: [10, 'r', 'ott'],
        11: [11, 'r', 'nov'],
        12: [12, 'r', 'dic'],
        'TOTAL': [13, 'r', 'TOTALE'],
        }
        
lm_journals = {
        'NAM_JRN': [0, '3l', '@v10'],
        1: [1, 'r', 'gen'],
        2: [2, 'r', 'feb'],
        3: [3, 'r', 'mar'],
        4: [4, 'r', 'apr'],
        5: [5, 'r', 'mag'],
        6: [6, 'r', 'giu'],
        7: [7, 'r', 'lug'],
        8: [8, 'r', 'ago'],
        9: [9, 'r', 'set'],
        10: [10, 'r', 'ott'],
        11: [11, 'r', 'nov'],
        12: [12, 'r', 'dic'],
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
    results = computeCashFlows(fiscalyearName,moveLineStark.DF,accountStark.DF,
                    periodStark.DF,linesDf,matchingsDf,onlyValidatedMoves,
                    defaultIncomingsFlowLineCode,defaultExpensesFlowLineCode,
                    printWarnings=True)
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    OUT_PATH = os.path.join(SRE_PATH, 'flussi_cassa')
    concatDf = pandas.concat([results['cashFlows'],results['diffEntUsc'],results['saldoAgg']])
    bagFlows = Bag(concatDf, os.path.join(OUT_PATH, 'cash_flows.pickle'), TI='tab',LM=lm_flussi)
    setattr(bagFlows,"YEAR",fiscalyearName)
    setattr(bagFlows,"COMPANY_STRING",companyString)
    setattr(bagFlows,"COMPANY",companyName)
    bagFlows.save()
    bagJournals = Bag(results['saldoJournals'], os.path.join(OUT_PATH, 'journals.pickle'), TI='tab',LM=lm_journals)
    bagJournals.save()
    return 0

###########
## funzioni di calcolo
###########

def checkAccounts(matchingsDf, accountsDf):
    '''
    controlla le corrispondenze tra i conti nel file della mappatura e i conti presenti nel db, evidenziando le eventuali differenze
    '''
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

#########
###funzioni private utilizzate per il calcolo dei flussi
#########
def _computeCashFlowFromPayableAccounts(cashFlowsDf, month, defaultExpensesFlowLineCode, payableMoveLineDf, moveLineDf, matchingsDf, totalReconcile ,printWarnings=False):
    '''
    funzione per il calcolo dei flussi di cassa da pagamenti su conti payable
    @param cashFlowsDf: è il dataframe con tutti i risultati dei flussi di cassa
    @param month: è un intero (da 1 a 12) che indica il mese dei flussi da calcolare
    @param defaultExpensesFlowLineCode: è il codice della voce dei flussi di default per le uscite
    @param payableMoveLineDf: è il df che contiene le move line relative ai pagamenti sui conti payable
    @param moveLineDf: è il df contenente tutte le move line
    @param matchingsDf: è il df contenente le mappature tra conti servabit e le voci dei flussi di cassa ("in entrata" e "in uscita")
    @param totalReconcile: è un booleano che indica se considerare i pagamenti con riconciliazione totale (=True) oppure parziale (=False)
    @param printWarnigns: è un booleano che indica se stampare o meno i messaggi di warning
    '''
    recParam = totalReconcile and "ID_REC" or "ID_REC_P"
    df8 = payableMoveLineDf.rename(columns={'CRT_MVL' : 'CRT_PAYED', 'DBT_MVL' : 'DBT_PAYED'})
    df8 = df8[["CRT_PAYED","DBT_PAYED",recParam,"ID0_MVL"]]
    df15 = moveLineDf.rename(columns={'CRT_MVL' : 'CRT_REC', 'DBT_MVL' : 'DBT_REC'})
    df9 = pandas.merge(df15,df8,on=recParam)
    df9 = df9[df9["ID0_MVL.x"]!=df9["ID0_MVL.y"]].reset_index(drop=True)
    del df9["ID0_MVL.y"]
    df9 = df9.rename(columns={'ID0_MVL.x' : 'ID_MVL'})
    df10 = df9[df9["CRT_REC"]>0].reset_index(drop=True)
    df11 = df9[(df9["CRT_REC"]==0) & (df9["DBT_REC"]==df9["CRT_PAYED"])].reset_index(drop=True)
    if len(df11)>0 and printWarnings:
        print "Errore c: le seguenti move line hanno importo di dare >0."+\
                "Verranno scartate dai flussi di cassa in quanto non possono rifersi ad un pagamento su un conto payable"
        print df11[["ID_MVL","DAT_MVL","NAM_MOV"]]
    if len(df10)>0:
        #calcolo percentuale riconciliata
        df10["percentage"] = df10["DBT_PAYED"]/df10["CRT_REC"]
        df10['percentage'] = numpy.where(df10['percentage']>1,1,df10['percentage'])
        _computeCashFlowFromReconcileFinalStep(cashFlowsDf,month,defaultExpensesFlowLineCode,df10,moveLineDf,matchingsDf,False,printWarnings=printWarnings)
        
def _computeCashFlowFromReceivableAccounts(cashFlowsDf, month, defaultIncomingsFlowLineCode, receivableMoveLineDf, moveLineDf, matchingsDf, totalReconcile ,printWarnings=False):
    '''
    funzione per il calcolo dei flussi di cassa da pagamenti su conti receivable
    @param cashFlowsDf: è il dataframe con tutti i risultati dei flussi di cassa
    @param month: è un intero (da 1 a 12) che indica il mese dei flussi da calcolare
    @param defaultIncomingsFlowLineCode: è il codice della voce dei flussi di default per le entrate
    @param receivableMoveLineDf: è il df che contiene le move line relative ai pagamenti sui conti receivable
    @param moveLineDf: è il df contenente tutte le move line
    @param matchingsDf: è il df contenente le mappature tra conti servabit e le voci dei flussi di cassa ("in entrata" e "in uscita")
    @param totalReconcile: è un booleano che indica se considerare i pagamenti con riconciliazione totale (=True) oppure parziale (=False)
    @param printWarnigns: è un booleano che indica se stampare o meno i messaggi di warning
    '''
    recParam = totalReconcile and "ID_REC" or "ID_REC_P"
    df8 = receivableMoveLineDf.rename(columns={'CRT_MVL' : 'CRT_PAYED', 'DBT_MVL' : 'DBT_PAYED'})
    df8 = df8[["CRT_PAYED","DBT_PAYED",recParam,"ID0_MVL"]]
    df15 = moveLineDf.rename(columns={'CRT_MVL' : 'CRT_REC', 'DBT_MVL' : 'DBT_REC'})
    df9 = pandas.merge(df15,df8,on=recParam)
    df9 = df9[df9["ID0_MVL.x"]!=df9["ID0_MVL.y"]].reset_index(drop=True)
    del df9["ID0_MVL.y"]
    df9 = df9.rename(columns={'ID0_MVL.x' : 'ID_MVL'})
    df10 = df9[df9["DBT_REC"]>0].reset_index(drop=True)
    df11 = df9[(df9["DBT_REC"]==0) & (df9["CRT_REC"]==df9["DBT_PAYED"])].reset_index(drop=True)
    if len(df11)>0 and printWarnings:
        print "Errore e: le seguenti move line hanno importo di avere >0."+\
                "Verranno scartate dai flussi di cassa in quanto non possono rifersi ad un pagamento su un conto receivable"
        print df11[["ID_MVL","DAT_MVL","NAM_MOV"]]
    if len(df10)>0:
        #calcolo percentuale riconciliata
        df10["percentage"] = df10["CRT_PAYED"]/df10["DBT_REC"]
        df10['percentage'] = numpy.where(df10['percentage']>1,1,df10['percentage'])
        _computeCashFlowFromReconcileFinalStep(cashFlowsDf,month,defaultIncomingsFlowLineCode,df10,moveLineDf,matchingsDf,True,printWarnings=printWarnings)
    
def _computeCashFlowFromReconcileFinalStep(cashFlowsDf, month, defaultFlowLine, reconcilesDf, moveLineDf, matchingsDf, amountInCredit, printWarnings=False):
    '''
    funzione dello step finale nel calcolo dei flussi di cassa provenienti da pagamenti su conti payable o receivable
    @param cashFlowsDf: è il dataframe con tutti i risultati dei flussi di cassa
    @param month: è un intero (da 1 a 12) che indica il mese dei flussi da calcolare
    @param defaultFlowLine: è il codice della voce dei flussi di default
    @param reconcilesDf: è il df che contiene le move line con le informazioni di riconciliazione
    @param moveLineDf: è il df contenente tutte le move line
    @param matchingsDf: è il df contenente le mappature tra conti servabit e le voci dei flussi di cassa ("in entrata" e "in uscita")
    @param amountInCredit: è un boolean. se True -> amount = credit - debit , se False -> viceversa
    @param printWarnigns: è un booleano che indica se stampare o meno i messaggi di warning
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
        cashFlowsDf[code][month] += amount
        
def _computeCashFlowFromMoveLine(cashFlowsDf, month, moveLineDf, matchingsDf, defaultIncomingsFlowLineCode, defaultExpensesFlowLineCode, printWarnings=False):
    '''
    funzione che calcola flussi di cassa provenienti da pagamenti in cui non sono presenti move line su conti payable o receivable
    @param cashFlowsDf: è il dataframe con tutti i risultati dei flussi di cassa
    @param month: è un intero (da 1 a 12) che indica il mese dei flussi da calcolare
    @param defaultIncomingsFlowLineCode: è il codice della voce dei flussi di default per le entrate
    @param defaultExpensesFlowLineCode: è il codice della voce dei flussi di default per le uscite
    @param moveLineDf: è il df contenente tutte le move line
    @param matchingsDf: è il df contenente le mappature tra conti servabit e le voci dei flussi di cassa ("in entrata" e "in uscita")
    @param printWarnigns: è un booleano che indica se stampare o meno i messaggi di warning
    '''
    df1 = pandas.merge(moveLineDf,matchingsDf,left_on="COD_CON",right_on="servabit_code")
    df2 = df1[df1["CRT_MVL"]>0].reset_index()
    for i in range(len(df2)):
        row = df2[i:i+1]
        code = row["entrata_code"][i]
        amount = row["CRT_MVL"][i]
        cashFlowsDf[code][month] += amount
        if printWarnings and code==defaultIncomingsFlowLineCode:
            print "Warning: la move.line "+row["NAM_MVL"][i].encode("utf8")+" sul conto="+\
                row["COD_CON"][i].encode("utf8")+", della move "+row["NAM_MOV"][i].encode("utf8")+\
                " non è riconciliata. L'importo è finito in altre entrate operative con importo "+str(row["CRT_MVL"][i])
    df3 = df1[df1["DBT_MVL"]>0].reset_index()
    for i in range(len(df3)):
        row = df3[i:i+1]
        code = row["uscita_code"][i]
        amount = row["DBT_MVL"][i]
        cashFlowsDf[code][month] += amount
        if printWarnings and code==defaultExpensesFlowLineCode:
            print "Warning: la move.line "+row["NAM_MVL"][i].encode("utf8")+" sul conto="+\
                row["COD_CON"][i].encode("utf8")+", della move "+row["NAM_MOV"][i].encode("utf8")+\
                " non è riconciliata. L'importo è finito in altre uscite operative con importo "+str(row["DBT_MVL"][i])
        

def computeCashFlows(fiscalyearName, moveLineDf, accountDf, periodDf, flowLinesDf,
                    matchingsDf, onlyValidatedMoves, defaultIncomingsFlowLineCode,
                    defaultExpensesFlowLineCode, printWarnings=True):
    '''
    funzione che calcola i flussi di cassa e i saldi suddivisi per journal. Restituisce un dizionario con le seguenti voci:
    'cashFlows' : è il df dei flussi di cassa
    'diffEntUsc' : è un df con la differenza tra entrate e uscite
    'saldoAgg' : è un df con il saldo aggregato
    'saldoJournals' : è un df con il saldo dei journals
    '''
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
    itemsList = []
    for el in incomingCodesList:
        t = (el,[0,0,0,0,0,0,0,0,0,0,0,0,0])
        itemsList.append(t)
    cashFlowsDf = pandas.DataFrame.from_items(itemsList)
    journalsDf = pandas.DataFrame()
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
            df3[month] = df3["DBT_MVL"] - df3["CRT_MVL"]
            if len(journalsDf)>0:
                df21 = pandas.merge(df3,journalsDf,on="NAM_JRN",how="outer")                
                del df21["DBT_MVL"]
                del df21["CRT_MVL"]
                journalsDf = df21
            else:
                journalsDf = df3[["NAM_JRN",month]]
            #calcolo flussi suddivisi in voci
            df4 = df2[["NAM_MOV","NAM_FY","NAM_JRN"]]
            if len(df4) > 0:
                df5 = pandas.merge(moveLineDf,df4,on=["NAM_MOV","NAM_FY","NAM_JRN"])
                df6 = df5[df5["TYP_CON"]!='liquidity'].reset_index(drop=True)
                ######
                ##flussi per conti 'payable'
                ######
                df7 = df6[df6["TYP_CON"]=='payable'].reset_index(drop=True)
                #con riconciliazione totale
                df8 = df7[df7["ID_REC"].notnull()]
                if len(df8) > 0:
                    _computeCashFlowFromPayableAccounts(cashFlowsDf,month,defaultExpensesFlowLineCode,
                                                        df8,moveLineDf,matchingsDf,True,printWarnings=printWarnings)
                #con riconciliazione parziale
                df8 = df7[df7["ID_REC_P"].notnull()]
                if len(df8) > 0:
                    _computeCashFlowFromPayableAccounts(cashFlowsDf,month,defaultExpensesFlowLineCode,
                                                        df8,moveLineDf,matchingsDf,False,printWarnings=printWarnings)
                #senza riconciliazione
                df8 = df7[(df7["ID_REC_P"].isnull()) & (df7["ID_REC"].isnull())]
                _computeCashFlowFromMoveLine(cashFlowsDf, month, df8, matchingsDf, 
                                            defaultIncomingsFlowLineCode, defaultExpensesFlowLineCode,printWarnings=printWarnings)
                ######
                ##flussi per conti 'receivable'
                ######
                df7 = df6[df6["TYP_CON"]=='receivable'].reset_index(drop=True)
                #con riconciliazione totale
                df8 = df7[df7["ID_REC"].notnull()]
                if len(df8) > 0:
                    _computeCashFlowFromReceivableAccounts(cashFlowsDf,month,defaultIncomingsFlowLineCode, 
                                                            df8, moveLineDf, matchingsDf, True ,printWarnings=printWarnings)
                #con riconciliazione parziale
                df8 = df7[df7["ID_REC_P"].notnull()]
                if len(df8) > 0:
                    _computeCashFlowFromReceivableAccounts(cashFlowsDf, month, defaultIncomingsFlowLineCode, 
                                                            df8, moveLineDf, matchingsDf, False ,printWarnings=printWarnings)
                #senza riconciliazione
                df8 = df7[(df7["ID_REC_P"].isnull()) & (df7["ID_REC"].isnull())]
                _computeCashFlowFromMoveLine(cashFlowsDf, month, df8, matchingsDf, 
                                            defaultIncomingsFlowLineCode, defaultExpensesFlowLineCode,printWarnings=printWarnings)
                ######
                ##flussi per conti non 'payable' né 'receivable'
                ######
                df7 = df6[(df6["TYP_CON"]!='receivable') & (df6["TYP_CON"]!='payable')].reset_index(drop=True)
                _computeCashFlowFromMoveLine(cashFlowsDf, month, df7, matchingsDf, 
                                            defaultIncomingsFlowLineCode, defaultExpensesFlowLineCode,printWarnings=printWarnings)
    #calcolo totali mensili
    cashFlowsDf = cashFlowsDf.transpose()
    columns = list(cashFlowsDf.columns)
    cashFlowsDf["TOTAL"] = 0
    for column in columns:
        cashFlowsDf["TOTAL"] += cashFlowsDf[column]
    columns = list(cashFlowsDf.columns)
    cashFlowsDf = cashFlowsDf.reset_index()
    #calcolo livello per ogni voce di flusso
    compute = True
    df1 = flowLinesDf[flowLinesDf["parent_id"].isnull()]
    count = 0
    df1["level"] = count
    dfFlowsWithLevel = df1
    while compute:
        count += 1
        df1 = df1[["Fl_Code"]]
        df1 = df1.rename(columns={'Fl_Code' : 'code'})
        df1 = pandas.merge(df1,flowLinesDf,left_on="code",right_on="parent_id")
        if len(df1)>0:
            df1["level"] = count
            del df1["code"]
            dfFlowsWithLevel = pandas.concat([dfFlowsWithLevel,df1]).reset_index(drop=True)
        else:
            compute=False
    #calcolo totali
    df3 = dfFlowsWithLevel[["Fl_Code","level"]]
    cashFlowsDf = pandas.merge(cashFlowsDf,df3,left_on="index",right_on="Fl_Code")
    del cashFlowsDf["Fl_Code"]
    df2 = cashFlowsDf[["level"]].drop_duplicates()
    maxLevel = int(max(list(df2["level"])))
    cashFlowsDf["USED_FOR_CALC"] = False
    for i in range(maxLevel):
        level = maxLevel - i
        df10 = cashFlowsDf[(cashFlowsDf["USED_FOR_CALC"]==False) & (cashFlowsDf["level"]==level)]
        df15 = cashFlowsDf[(cashFlowsDf["USED_FOR_CALC"]==True) | (cashFlowsDf["level"]!=level)]
        if len(df10)>0:
            df10["USED_FOR_CALC"] = True
            df11 = pandas.merge(df10,dfFlowsWithLevel,left_on="index",right_on="Fl_Code")
            df12 = df11.groupby("parent_id").sum()[columns].reset_index()
            df12 = df12.rename(columns={'parent_id' : 'index'})
            df12["USED_FOR_CALC"] = False
            df12["level"] = level-1
            cashFlowsDf = pandas.concat([df10,df12,df15]).reset_index(drop=True)
    cashFlowsDf = cashFlowsDf.rename(columns={'index' : 'Fl_Code'})
    df5 = flowLinesDf[["Fl_Code","descrizione"]].reset_index()
    cashFlowsDf = pandas.merge(df5,cashFlowsDf,on="Fl_Code",how="left")
    cashFlowsDf = cashFlowsDf[["Fl_Code","descrizione",1,2,3,4,5,6,7,8,9,10,11,12,"TOTAL","index"]]
    journalDfColumns = list(journalsDf.columns)
    for i in range(12):
        c = i+1
        cashFlowsDf[c].ix[cashFlowsDf[c].isnull()] = 0
        if journalDfColumns.count(c) > 0:
            journalsDf[c].ix[journalsDf[c].isnull()] = 0
        else:
            journalsDf[c] = 0
    cashFlowsDf["TOTAL"].ix[cashFlowsDf["TOTAL"].isnull()] = 0
    cashFlowsDf = cashFlowsDf.sort(['index']).reset_index(drop=True)
    del cashFlowsDf["index"]
    del cashFlowsDf["Fl_Code"]
    #calcolo diff ent/usc
    diffEntUsc = journalsDf.copy()
    diffEntUsc["NAM_JRN"] = 'ciccio'
    diffEntUsc = diffEntUsc.groupby("NAM_JRN").sum().reset_index()
    del diffEntUsc["NAM_JRN"]
    diffEntUsc["TOTAL"] = 0
    for i in range(12):
        month = i+1
        diffEntUsc["TOTAL"] += diffEntUsc[month]
    diffEntUsc["descrizione"] = 'Differenza Ent/Usc'
    #calcolo saldo journals
    for i in range(11):
        month = i+2
        journalsDf[month] += journalsDf[month-1]
    #calcolo saldo aggregato
    saldoAgg = journalsDf.copy()
    saldoAgg["NAM_JRN"] = 'ciccio'
    saldoAgg = saldoAgg.groupby("NAM_JRN").sum().reset_index()
    saldoAgg["descrizione"] = 'Saldo aggregato'
    saldoAgg["TOTAL"] = ''
    return {
        'cashFlows' : cashFlowsDf,
        'diffEntUsc' : diffEntUsc,
        'saldoAgg' : saldoAgg,
        'saldoJournals' : journalsDf,
        }
                
    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))