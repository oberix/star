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
import os
import sys
import pandas
from stark import StarK
from decimal import Decimal
import numpy


def getVatRegister(picklesPath, companyName, onlyValidatedMoves, sequenceName=None, periodName=None, fiscalyearName=None):
    '''
    funzione per il calcolo dei registri iva
    '''
    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")
    
    companyPathPkl = os.path.join(picklesPath,companyName)
    
    starkTax=StarK.Loadk(companyPathPkl,"TAX.pickle")
    starkMoveLine=StarK.Loadk(companyPathPkl,"MVL.pickle")
    df0 = starkMoveLine.DF
    del df0["ID0_MVL"]
    del df0["CHK_MOV"]
    del df0["NAM_REC"]
    del df0["NAM_REC_P"]
    del df0["CRT_MVL"]
    del df0["DBT_MVL"]
    del df0["NAM_CON"]
    del df0["NAM_JRN"]
    del df0["NAM_MVL"]
    del df0["REF_MVL"]    
    
    if sequenceName:
        df0 = df0.ix[df0['NAM_SEQ']==sequenceName]
    df1 = df0.ix[(df0['TAX_COD'].notnull()) & (df0['COD_SEQ']=='RIVA')]
    if periodName:
        df1 = df1.ix[df1['NAM_PRD']==periodName]
    else:
        df1 = df1.ix[df1['NAM_FY']==fiscalyearName]
    if onlyValidatedMoves:
        df1 = df1.ix[df0['STA_MOV']=='posted']
    df1 = df1.reset_index(drop=True)
    for i in range(len(df1)):
        row = df1[i:i+1]
        moveName = row['NAM_MOV'][i]
        moveNameSplits = moveName.split("/")
        df1[i:i+1]['NAM_MOV'] = moveNameSplits[len(moveNameSplits)-1]
    df1 = df1.sort(['DAT_MVL','NAM_MOV'])
    del df1['STA_MOV']
    del df1['NAM_FY']
    del df1['NAM_SEQ']
    del df1['NAM_PRD']
    del df1["COD_SEQ"]
    #merge con tasse a seconda del journal type
    df2 = df1[df1['TYP_JRN'].isin(['sale', 'purchase'])]
    df3 = pandas.merge(df2,starkTax.DF,how='left',left_on='TAX_COD',right_on='TAX_CODE')

    df4 = df1[df1['TYP_JRN'].isin(['sale_refund', 'purchase_refund'])]
    df5 = pandas.merge(df4,starkTax.DF,how='left',left_on='TAX_COD',right_on='REF_TAX_CODE')

    #concatenazione dei due df precedenti
    df6 = pandas.concat([df3,df5])
    df6 = df6.reset_index(drop=True)
    df6['ST_TAX'] = 'TAX'
    df6['ST_TAX'].ix[df6['NAM_TAX'].isnull()] = 'BASE'
    df6 = df6.reset_index()

    #aggregazione delle righe per tax_code uguale nella stessa move
    df6['BASE_CODE'].ix[df6['BASE_CODE'].isnull()] = "-1"
    df6['NAM_TAX'].ix[df6['NAM_TAX'].isnull()] = "NULL"
    df6['REF_BASE_CODE'].ix[df6['REF_BASE_CODE'].isnull()] = "-1"
    df6['REF_TAX_CODE'].ix[df6['REF_TAX_CODE'].isnull()] = "-1"
    df6['TAX_CODE'].ix[df6['TAX_CODE'].isnull()] = "-1"
    del df6["index"]
    groupbyCols = list(df6.columns)
    groupbyCols.remove('TAX_AMO')
    df7 = df6.groupby(groupbyCols).sum()[['TAX_AMO']].reset_index()
    df7['TAX_AMO']=df7['TAX_AMO'].map(float)
    df7['BASE_CODE']=df7['BASE_CODE'].map(int)
    df7['REF_BASE_CODE']=df7['REF_BASE_CODE'].map(int)
    df7['REF_TAX_CODE']=df7['REF_TAX_CODE'].map(int)
    df7['TAX_CODE']=df7['TAX_CODE'].map(int)

    #aggiunta colonne BASE e TAX con importi di imponibile e imposta a seconda delle righe
    df8 = pandas.pivot_table(df7,values='TAX_AMO', cols=['ST_TAX'], rows=['NAM_MOV','NAM_TAX','TAX_COD','BASE_CODE','REF_BASE_CODE','TYP_JRN','COD_CON'])
    df8 = df8.reset_index()

    df9 = df8.ix[df8['NAM_TAX']!='NULL']
    df9 = df9.reset_index(drop=True)
    for i in range(len(df9)):
        row = df9[i:i+1]
        moveName = row['NAM_MOV'][i]
        baseCode = row['BASE_CODE'][i]
        refBaseCode = row['REF_BASE_CODE'][i]
        journalType = row['TYP_JRN'][i]
        df10 = None
        if journalType in ['sale','purchase']:
            df10 = df8.ix[df8['NAM_MOV']==moveName].ix[df8['TAX_COD']==baseCode]
        else:
            df10 = df8.ix[df8['NAM_MOV']==moveName].ix[df8['TAX_COD']==refBaseCode]
        df10 = df10.reset_index(drop=True)
        df9[i:i+1]['BASE'] = df10[0:1]['BASE'][0]
        
    del df9['TAX_COD']
    del df9['BASE_CODE']
    del df9['REF_BASE_CODE']
    del df9['TYP_JRN']

    del df7['TAX_COD']
    del df7['TYP_JRN']
    del df7['BASE_CODE']
    del df7['REF_BASE_CODE']
    del df7['REF_TAX_CODE']
    del df7['ST_TAX']
    del df7['TAX_AMO']
    del df7['TAX_CODE']
    del df7['NAM_TAX']
    df7 = df7.drop_duplicates()
    
    df10 = pandas.merge(df7,df9,on=["NAM_MOV","COD_CON"])
    df10 = df10.sort(['DAT_MVL','NAM_MOV'])
    df10 = df10.reset_index(drop=True)
    previousMoveName = ""
    for i in range(len(df10)):
        row = df10[i:i+1]
        moveName = row['NAM_MOV'][i]
        if moveName==previousMoveName:
            df10[i:i+1]['DAT_DOC'] = ''
            df10[i:i+1]['DAT_MVL'] = ''
            df10[i:i+1]['NAM_MOV'] = ''
            df10[i:i+1]['NAM_PAR'] = ''
            df10[i:i+1]['REF_MOV'] = ''
        previousMoveName = moveName
    vatRegister = df10[['DAT_MVL','NAM_MOV','DAT_DOC','REF_MOV','NAM_PAR','NAM_TAX','BASE','TAX','COD_CON']]
    return vatRegister


def getVatSummary(picklesPath, companyName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, sequenceName=None, periodName=None, fiscalyearName=None):
    '''
    funzione per il calcolo dei riepiloghi iva
    '''
    df1 = getVatRegister(picklesPath, companyName, onlyValidatedMoves, periodName=periodName, fiscalyearName=fiscalyearName, sequenceName=sequenceName)
    del df1['DAT_MVL']
    del df1['NAM_MOV']
    del df1['DAT_DOC']
    del df1['REF_MOV']
    del df1['NAM_PAR']
    
    df1['DETRAIB'] = True
    df1['DETRAIB'].ix[(df1['COD_CON']!=immediateVatCreditAccountCode) &
                            (df1['COD_CON']!=immediateVatDebitAccountCode) &
                            (df1['COD_CON']!=deferredVatCreditAccountCode) &
                            (df1['COD_CON']!=deferredVatDebitAccountCode)
                            ] = False
    df1['IMMED'] = True
    df1['IMMED'].ix[(df1['COD_CON']==deferredVatCreditAccountCode) |
                    (df1['COD_CON']==deferredVatDebitAccountCode)
                    ] = False
    df1['CREDIT'] = True
    df1['CREDIT'].ix[(df1['COD_CON']==immediateVatDebitAccountCode) |
                    (df1['COD_CON']==deferredVatDebitAccountCode)
                    ] = False
    del df1['COD_CON']
    groupbyCols = list(df1.columns)
    groupbyCols.remove('BASE')
    groupbyCols.remove('TAX')
    df1 = df1.groupby(groupbyCols).sum()[['BASE','TAX']].reset_index()
    
    def addTotalRow(df,detraib=None,immed=None,credit=None):
        tempDf = df
        if detraib is not None:
            tempDf = tempDf.ix[(tempDf['DETRAIB']==detraib)]
        else:
            tempDf = tempDf.ix[(tempDf['NAM_TAX']!='Totale')]
            tempDf['DETRAIB'] = 'Null'
        if immed is not None:
            tempDf = tempDf.ix[(tempDf['IMMED']==immed)]
        else:
            tempDf = tempDf.ix[(tempDf['NAM_TAX']!='Totale')]
            tempDf['IMMED'] = "Null"
        if credit is not None:
            tempDf = tempDf.ix[(tempDf['CREDIT']==credit)]
        else:
            tempDf = tempDf.ix[(tempDf['NAM_TAX']!='Totale')]
            tempDf['CREDIT'] = "Null"
        del tempDf['NAM_TAX']
        groupbyCols = list(tempDf.columns)
        groupbyCols.remove('BASE')
        groupbyCols.remove('TAX')
        tempDf = tempDf.groupby(groupbyCols).sum()[['BASE','TAX']].reset_index()
        tempDf['NAM_TAX'] = "Totale"
        df = pandas.concat([df,tempDf])
        df = df.reset_index(drop=True)
        return df
    
    #aggiunta totale iva immediata a credito
    df1 = addTotalRow(df1,detraib=True,immed=True,credit=True)
    #aggiunta totale iva immediata a debito
    df1 = addTotalRow(df1,detraib=True,immed=True,credit=False)
    #aggiunta totale iva differita a credito
    df1 = addTotalRow(df1,detraib=True,immed=False,credit=True)
    #aggiunta totale iva differita a debito
    df1 = addTotalRow(df1,detraib=True,immed=False,credit=False)
    #aggiunta totale iva detraibile a credito
    df1 = addTotalRow(df1,detraib=True,credit=True)
    #aggiunta totale iva detraibile a debito
    df1 = addTotalRow(df1,detraib=True,credit=False)
    #aggiunta totale iva indetraibile a credito
    df1 = addTotalRow(df1,detraib=False,immed=True,credit=True)
    #aggiunta totale iva indetraibile a debito
    df1 = addTotalRow(df1,detraib=False,immed=True,credit=False)
    #aggiunta totale iva detraibile + indetraibile a credito
    df1 = addTotalRow(df1,credit=True)
    #aggiunta totale iva detraibile + indetraibile a debito
    df1 = addTotalRow(df1,credit=False)
    
    return df1

def getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, searchPayments=False, periodName=None, fiscalyearName=None):
    '''
    funzione che restituisce l'iva differita o da pagare per il periodo (o l'anno fiscale) passati come parametro
    se searchPayments è True, si stanno cercando le fatture che sono state pagate nel periodo (o anno fiscale)
    se searchPayments è False, si stanno cercando le fatture che non sono state ancora pagate entro il periodo (o anno fiscale)
    '''
    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")
    
    companyPathPkl = os.path.join(picklesPath,companyName)
    
    starkTax=StarK.Loadk(companyPathPkl,"TAX.pickle")
    starkPeriod=StarK.Loadk(companyPathPkl,"PERIOD.pickle")
    starkMoveLine=StarK.Loadk(companyPathPkl,"MVL.pickle")
    df0 = starkMoveLine.DF
    df1 = df0.ix[(df0['COD_CON']==deferredVatCreditAccountCode) | (df0['COD_CON']==deferredVatDebitAccountCode)]
    if onlyValidatedMoves:
        df1 = df1.ix[df0['STA_MOV']=='posted']

    df1['TAX_COD'].ix[df1['TAX_COD'].isnull()] = 'NULL'
    df1 = pandas.merge(df1,starkTax.DF,how='left',left_on='TAX_COD',right_on='TAX_CODE')
    for i in range(len(df1)):
        row = df1[i:i+1]
        moveName = row['NAM_MOV'][i]
        moveNameSplits = moveName.split("/")
        df1[i:i+1]['NAM_MOV'] = moveNameSplits[len(moveNameSplits)-1]
    del df1["ID0_MVL"]
    del df1["STA_MOV"]
    del df1["DAT_DOC"]
    del df1["CHK_MOV"]
    del df1["TAX_AMO"]
    del df1["TYP_JRN"]
    del df1["NAM_CON"]
    del df1["NAM_JRN"]
    del df1["NAM_MVL"]
    del df1["REF_MVL"]
    del df1["REF_MOV"]
    del df1["TAX_COD"]
    del df1["TAX_CODE"]
    del df1["BASE_CODE"]
    del df1["REF_TAX_CODE"]
    del df1["REF_BASE_CODE"]
    
    df2 = None
    
    if searchPayments:
        df2 = df1.ix[(df1['NAM_REC'].notnull()) | (df1['NAM_REC_P'].notnull())]
        dfWithPayments = None
        if periodName:
            dfWithPayments = df2.ix[df2['NAM_PRD']==periodName]
        else:
            dfWithPayments = df2.ix[df2['NAM_FY']==fiscalyearName]
        dfWithPayments = dfWithPayments.ix[
            ((dfWithPayments['COD_CON']==deferredVatCreditAccountCode) & (dfWithPayments['CRT_MVL']>0)) | 
            ((dfWithPayments['COD_CON']==deferredVatDebitAccountCode) & (dfWithPayments['DBT_MVL']>0))
            ]
        dfWithPayments['DBT_MVL']=dfWithPayments['DBT_MVL'].map(float)
        dfWithPayments['CRT_MVL']=dfWithPayments['CRT_MVL'].map(float)
        dfWithPayments['AMO'] = numpy.where(dfWithPayments['CRT_MVL'] > 0.0, dfWithPayments['CRT_MVL'], dfWithPayments['DBT_MVL'])
        dfWithPayments = dfWithPayments[['NAM_REC','NAM_REC_P','DAT_MVL','AMO']]
        dfWithPayments = dfWithPayments.rename(columns={'DAT_MVL' : 'DAT_PAY'})
        dfWithoutPayments = df2.ix[
            ((df2['COD_CON']==deferredVatCreditAccountCode) & (df2['DBT_MVL']>0)) |
            ((df2['COD_CON']==deferredVatDebitAccountCode) & (df2['CRT_MVL']>0))
            ]
        dfWithoutPayments['CREDIT'] = False
        dfWithoutPayments['CREDIT'].ix[dfWithoutPayments['DBT_MVL'] > 0] = True
        dfWithoutPayments = dfWithoutPayments[['DAT_MVL','NAM_PAR','NAM_TAX','NAM_MOV','NAM_SEQ','NAM_REC','NAM_REC_P','CREDIT']]
        dfWithoutPayments['NAM_REC'].ix[dfWithoutPayments['NAM_REC'].isnull()] = 'NULL'
        dfWithoutPayments['NAM_REC_P'].ix[dfWithoutPayments['NAM_REC_P'].isnull()] = 'NULL'
        df2 = pandas.merge(dfWithPayments,dfWithoutPayments,on='NAM_REC')
        df3 = pandas.merge(dfWithPayments,dfWithoutPayments,on='NAM_REC_P')
        df2 = pandas.concat([df2,df3])
        df2 = df2[['AMO','DAT_MVL','NAM_MOV','NAM_PAR','NAM_SEQ','NAM_TAX','CREDIT','DAT_PAY']]
    #else: si stanno cercando le fatture con esigibilità differita non ancora pagate
    else:
        dfPeriods = starkPeriod.DF
        dateStop = None
        if periodName:
            df10 = dfPeriods.ix[dfPeriods['NAM_PRD']==periodName]
            df10 = df10.reset_index()
            dateStop = df10['P_DAT_STOP'][0]
        else:
            df10 = dfPeriods.ix[dfPeriods['NAM_FY']==fiscalyearName]
            df10 = df10.reset_index()
            dateStop = df10[0:1]['FY_DAT_STOP'][0]
        #calcolo delle fatture ad esig. diff. non riconciliate e non parzialmente riconciliate entro il periodo d'interesse
        df2 = df1.ix[(df1['NAM_REC'].isnull()) & (df1['NAM_REC_P'].isnull()) & (df1['COD_SEQ']=='RIVA') & (df1['DAT_MVL'] <= dateStop)]
        df2.reset_index()
        
        #calcolo delle fatture ad esig. diff. totalmente riconciliate ma il cui pagamento è successivo al periodo d'interesse
        df3 = df1.ix[((df1['NAM_REC'].notnull()) | (df1['NAM_REC_P'].notnull())) & (df1['COD_SEQ']=='RIVA') & (df1['DAT_MVL'] <= dateStop)]
        dfWithPayments = df1.ix[((df1['NAM_REC'].notnull()) | (df1['NAM_REC_P'].notnull())) & (df1['DAT_MVL'] <= dateStop)]        
        dfWithPayments = dfWithPayments.ix[
            ((dfWithPayments['COD_CON']==deferredVatCreditAccountCode) & (dfWithPayments['CRT_MVL']>0)) | 
            ((dfWithPayments['COD_CON']==deferredVatDebitAccountCode) & (dfWithPayments['DBT_MVL']>0))
            ]
        dfWithPayments['DBT_MVL']=dfWithPayments['DBT_MVL'].map(float)
        dfWithPayments['CRT_MVL']=dfWithPayments['CRT_MVL'].map(float)
        dfWithPayments['AMO_PAY'] = numpy.where(dfWithPayments['CRT_MVL'] > 0.0, dfWithPayments['CRT_MVL'], dfWithPayments['DBT_MVL'])
        dfWithPayments = dfWithPayments[['NAM_REC','NAM_REC_P','DAT_MVL','AMO_PAY']]
        dfWithPayments = dfWithPayments.rename(columns={'DAT_MVL' : 'DAT_PAY'})
        #aggiunta delle fatture senza pagamenti totali entro il periodo
        if len(dfWithPayments)>0 and len(df3)>0:
            df5 = dfWithPayments.ix[(dfWithPayments['NAM_REC'].notnull())]
            df4 = pandas.merge(df3,df5,on='NAM_REC',how='left')
            df4 = df4.ix[(df4['DAT_PAY'].isnull()) & (df4['NAM_REC'].notnull())]
            if len(df4)>0:
                del df4['DAT_PAY']
                df2 = pandas.concat([df2,df4])
                df2 = df2.reset_index(drop=True)
        
        df2['DBT_MVL']=df2['DBT_MVL'].map(float)
        df2['CRT_MVL']=df2['CRT_MVL'].map(float)
        df2['AMO'] = numpy.where(df2['CRT_MVL'] > 0.0, df2['CRT_MVL'], df2['DBT_MVL'])
        #aggiunta delle fatture non totalmente pagate entro il periodo
        if len(dfWithPayments)>0:
            df5 = dfWithPayments.ix[(dfWithPayments['NAM_REC_P'].notnull())]
            df5 = df5.groupby('NAM_REC_P').sum()[['AMO_PAY']].reset_index()
            if len(df3)>0 and len(df5)>0:
                df4 = pandas.merge(df3,df5,on='NAM_REC_P')
                df4['DBT_MVL']=df4['DBT_MVL'].map(float)
                df4['CRT_MVL']=df4['CRT_MVL'].map(float)
                df4['AMO'] = numpy.where(df4['CRT_MVL'] > 0.0, df4['CRT_MVL']-df4['AMO_PAY'], df4['DBT_MVL']-df4['AMO_PAY'])
                df2 = pandas.concat([df2,df4])
                df2 = df2.reset_index(drop=True)
        #ultimi ritocchi
        df2['CREDIT'] = False
        df2['CREDIT'].ix[df2['DBT_MVL'] > 0] = True
        df2 = df2[['AMO','DAT_MVL','NAM_MOV','NAM_PAR','NAM_SEQ','NAM_TAX','CREDIT']]
    return df2.sort(['NAM_SEQ','DAT_MVL','NAM_MOV'])
    

def getDeferredVatSummary(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, periodName=None, fiscalyearName=None):
    '''
    funzione che restituisce il riepilogo dell'iva differita.
    Il periodo (o l'anno fiscale) deve essere passato come parametro
    '''
    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")
    payments = getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, searchPayments=True, periodName=periodName)
    notPayed = getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, searchPayments=False, periodName=periodName)
    payments = payments[['AMO','NAM_TAX','NAM_SEQ','CREDIT']]
    notPayed = notPayed[['AMO','NAM_TAX','NAM_SEQ','CREDIT']]
    payments['PAYM'] = True
    notPayed['PAYM'] = False
    
    df1 = pandas.concat([payments,notPayed])
    df1 = df1.reset_index(drop=True)
    df1 = df1.sort(['NAM_SEQ'])
    df2 = None
    if len(df1) > 0:
        df2 = df1.groupby(['NAM_TAX','PAYM','CREDIT','NAM_SEQ']).sum()[['AMO']].reset_index()
        df2 = df2.sort(['NAM_SEQ'])
        df3 = df2[['NAM_SEQ']]
        df3 = df3.drop_duplicates()
        sequences = list(df3['NAM_SEQ'])
        
        def addTotalRow(df,searchPayments,credit,sequenceName=None):
            tempDf = df.ix[(df['PAYM']==searchPayments) & (df['CREDIT']==credit)]
            if sequenceName:
                tempDf = tempDf.ix[tempDf['NAM_SEQ']==sequenceName]
            else:
                tempDf = tempDf.ix[tempDf['NAM_TAX']=='Totale']
                tempDf['NAM_SEQ'] = 'Sintesi'
            del tempDf['NAM_TAX']
            if len(tempDf)>0:
                tempDf = tempDf.groupby(['PAYM','CREDIT','NAM_SEQ']).sum()[['AMO']].reset_index()
                tempDf['NAM_TAX'] = "Totale"
                df = pandas.concat([df,tempDf])
                df = df.reset_index(drop=True)
            return df
        #aggiunta totali per ogni sequenza    
        for sequence in sequences:
            df2 = addTotalRow(df2,True,True,sequence)
            df2 = addTotalRow(df2,True,False,sequence)
            df2 = addTotalRow(df2,False,True,sequence)
            df2 = addTotalRow(df2,False,False,sequence)
        #aggiunta totali di sintesi
        df2 = addTotalRow(df2,True,True)
        df2 = addTotalRow(df2,True,False)
        df2 = addTotalRow(df2,False,True)
        df2 = addTotalRow(df2,False,False)
    return df2

def _appendLineToVatLiquidationDict(liqDict, text, namSeq, dbt, crt):
    liqDict['TEXT'].append(text)
    liqDict['NAM_SEQ'].append(namSeq)
    liqDict['DBT'].append(dbt)
    liqDict['CRT'].append(crt)

def addLiquidationSummaryFinalResults(liquidationDict, moveLineDf, periodDf, debitVat, creditVat, companyName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode, periodName=None, fiscalyearName=None):
    #aggiunta riga "IVA a debito o credito per il periodo"
    if debitVat >= creditVat:
        _appendLineToVatLiquidationDict(liquidationDict, "IVA a debito o credito per il periodo", "", debitVat-creditVat, 0)
    else:
        _appendLineToVatLiquidationDict(liquidationDict, "IVA a debito o credito per il periodo", "", 0, creditVat-debitVat)
    #aggiunta riga "Debito (non superiore a 25,82 Euro) o credito da periodo precedente + acconti IVA"
    df0 = moveLineDf.ix[moveLineDf["COD_CON"]==treasuryVatAccountCode]
    if periodName:
        df1 = periodDf.ix[periodDf['NAM_PRD']==periodName].reset_index()
        dateStart = df1[0:1]['FY_DAT_STR'][0]
        dateStop = df1[0:1]['P_DAT_STOP'][0]
        df0 = df0.ix[(df0['DAT_MVL']>=dateStart) & (df0['DAT_MVL']<=dateStop)]
    else:
        df0 = df0.ix[df0['NAM_FY']==fiscalyearName]
    df0 = df0.reset_index(drop=True)
    df0 = df0[['COD_CON','DBT_MVL','CRT_MVL']]
    df0 = df0.groupby('COD_CON').sum()[['CRT_MVL','DBT_MVL']].reset_index()
    debitFromPreviousPeriod = df0[0:1]['DBT_MVL'][0]
    creditFromPreviousPeriod = df0[0:1]['CRT_MVL'][0]
    debitVat += debitFromPreviousPeriod
    creditVat += creditFromPreviousPeriod
    if debitFromPreviousPeriod >= creditFromPreviousPeriod:
        _appendLineToVatLiquidationDict(liquidationDict, "Debito (non superiore a 25,82 Euro) o credito da periodo precedente + acconti IVA", "", debitFromPreviousPeriod-creditFromPreviousPeriod, 0)
    else:
        _appendLineToVatLiquidationDict(liquidationDict, "Debito (non superiore a 25,82 Euro) o credito da periodo precedente + acconti IVA", "", 0, creditFromPreviousPeriod-debitFromPreviousPeriod)
    #aggiunta riga "IVA DOVUTA O A CREDITO PER IL PERIODO"
    if debitVat >= creditVat:
        _appendLineToVatLiquidationDict(liquidationDict, "IVA DOVUTA O A CREDITO PER IL PERIODO", "", debitVat-creditVat, 0)
    else:
        _appendLineToVatLiquidationDict(liquidationDict, "IVA DOVUTA O A CREDITO PER IL PERIODO", "", 0, creditVat-debitVat)
    #eventuale aggiunta ultime righe
    if debitVat > creditVat:
        interests = (debitVat-creditVat)/100
        _appendLineToVatLiquidationDict(liquidationDict, "Interessi (1%)", "", interests, 0)
        vatWithIntererest = debitVat -creditVat + interests
        _appendLineToVatLiquidationDict(liquidationDict, "IVA DOVUTA PER IL PERIODO CON INTERESSI", "", vatWithIntererest, 0)
    

def getVatLiquidationSummary(picklesPath, companyName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode, periodName=None, fiscalyearName=None):
    '''
    funzione che restituisce il riepilogo di liquidazione iva
    Il periodo (o l'anno fiscale) deve essere passato come parametro
    '''
    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")
    vatLiquidationDict = {
        'TEXT': [],
        'NAM_SEQ': [],
        'DBT': [],
        'CRT': [],
        }
    #recupero il nome delle sequenze iva per cui ci sono dei movimenti nel periodo d'interesse
    companyPathPkl = os.path.join(picklesPath,companyName)
    starkMoveLine=StarK.Loadk(companyPathPkl,"MVL.pickle")
    starkPeriod=StarK.Loadk(companyPathPkl,"PERIOD.pickle")
    df0 = starkMoveLine.DF
    df0 = df0.ix[df0['COD_SEQ']=='RIVA']
    if periodName:
        df0 = df0.ix[df0['NAM_PRD']==periodName]
    else:
        df0 = df0.ix[df0['NAM_FY']==fiscalyearName]
    df0 = df0[['NAM_SEQ']]
    df0 = df0.drop_duplicates()
    vatSequences = list(df0['NAM_SEQ'])
    #definizione variabili per totali iva a credito e a debito
    creditVatTotal = 0
    debitVatTotal = 0
    #recupero informazioni riepiloghi iva (per iva immediata)
    for sequence in vatSequences:
        vatSummary = getVatSummary(picklesPath, companyName, sequence, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, periodName=periodName)
        immediateDebitTotal = 0
        immediateCreditTotal = 0
        immediateDebitDf = vatSummary.ix[(vatSummary['IMMED']==True) & (vatSummary['CREDIT']==False) & (vatSummary['DETRAIB']==True) & (vatSummary['NAM_TAX']=='Totale')].reset_index()
        immediateCreditDf = vatSummary.ix[(vatSummary['IMMED']==True) & (vatSummary['CREDIT']==True) & (vatSummary['DETRAIB']==True) & (vatSummary['NAM_TAX']=='Totale')].reset_index()
        if len(immediateDebitDf)>0:
            immediateDebitTotal = immediateDebitDf[0:1]['TAX'][0]
        if len(immediateCreditDf)>0:    
            immediateCreditTotal = immediateCreditDf[0:1]['TAX'][0]
        _appendLineToVatLiquidationDict(vatLiquidationDict,"IVA ad esigibilita' immediata",sequence,immediateDebitTotal,immediateCreditTotal)
        creditVatTotal += immediateCreditTotal
        debitVatTotal += immediateDebitTotal
    #recupero informazioni per iva ad esig. differita
    deferredCreditTotal = 0
    deferredDebitTotal = 0
    deferredSummary = getDeferredVatSummary(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, periodName=periodName, fiscalyearName=fiscalyearName)
    if deferredSummary:
        deferredCreditDf = deferredSummary.ix[(deferredSummary['NAM_TAX']=='Totale') & (deferredSummary['NAM_SEQ']=='Sintesi') & (deferredSummary['PAYM']==True) & (deferredSummary['CREDIT']==True)].reset_index()
        deferredDebitDf = deferredSummary.ix[(deferredSummary['NAM_TAX']=='Totale') & (deferredSummary['NAM_SEQ']=='Sintesi') & (deferredSummary['PAYM']==True) & (deferredSummary['CREDIT']==False)].reset_index()
        if len(deferredCreditDf) > 0:
            deferredCreditTotal = deferredCreditDf[0:1]['AMO'][0]
        if len(deferredDebitDf) > 0:
            deferredDebitTotal = deferredDebitDf[0:1]['AMO'][0]    
    _appendLineToVatLiquidationDict(vatLiquidationDict,"IVA esigibile da esigibilita' differita","",deferredDebitTotal,deferredCreditTotal)
    creditVatTotal += deferredCreditTotal
    debitVatTotal += deferredDebitTotal
    _appendLineToVatLiquidationDict(vatLiquidationDict,"Totale","",debitVatTotal,creditVatTotal)
    #aggiunta righe finali
    addLiquidationSummaryFinalResults(vatLiquidationDict, starkMoveLine.DF, starkPeriod.DF, debitVatTotal, creditVatTotal, companyName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode, periodName=periodName, fiscalyearName=fiscalyearName)
    return pandas.DataFrame(vatLiquidationDict)