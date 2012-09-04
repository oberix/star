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
from decimal import Decimal
from datetime import date
import numpy
from share import Stark

def GroupInterOrd(group):
    group['ORD']=range(len(group))
    S=group
    return S    

def getVatRegister(vatDf, companyName, onlyValidatedMoves, sequenceName=None, periodName=None, fiscalyearName=None):
    '''
    funzione per il calcolo dei registri iva
    @param vatDf: è il dataframe contenente le informazioni specifiche per i report iva
    @param onlyValidatedMoves: booleano che indica se filtrare solo le scritture validate oppure no
    
    Nel porgramma vengono usate le seguenti variabili
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
    '''
    #definisco la lista delle variabili di interesse, da tenere nel corso del programma
    LVAR=['DATE','M_NUM','DATE_DOC','M_REF','PARTNER','T_NAME','BASE','TAX','T_CRED','T_DET','T_IMM','T_EXI']

    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")

    df0 = vatDf.copy(deep=True)
    # seleziono le scritture che soddisfano i criteri dati come imput
    if sequenceName:
        df0 = df0.ix[df0['SEQUENCE']==sequenceName]
    if periodName:
        df0 = df0.ix[df0['PERIOD']==periodName]
    else:
        df0 = df0.ix[df0['ESER']==fiscalyearName]
    if onlyValidatedMoves:
        df0 = df0.ix[df0['STATE']=='posted']
    #fine selezione
    df1 = df0.reset_index(drop=True)

    if len(df1)>0:
        df6 = df1.sort(['DATE','M_NUM']).reset_index(drop=True)
        #pulisco il database di eventuali casi in cui ho all'interno di una scrittura
        #più linee riguardanti la stessa imposta
        #calcolo la somma per ogni move delle imposte e dell'imponibile per ciascuna tassa
        G001 = ['M_NUM','T_NAME','T_TAX']
        df7 = df6.groupby(G001).sum()[['AMOUNT']].reset_index()
        df7['AMOUNT']=df7['AMOUNT'].map(float)
        #fine pulizie
        #isolo le imposte dalla base imponibile e tiporto le due variabili in colonna
        df7['ST_TAX'] = 'TAX'
        df7['ST_TAX'].ix[df7['T_TAX']==False] = 'BASE'
        #aggiunta colonne BASE e TAX con importi di imponibile e imposta a seconda delle righe
        df8 = pandas.pivot_table(df7,values='AMOUNT', cols=['ST_TAX'], 
                        rows=['M_NUM','T_NAME'])
        df8 = df8.reset_index()
        #in df8 ci sono le imposte e la base imponibile in colonna. 
        #la chiave univoca che identifica ciascuna riga è composta 
        #dal nome della move (M_NUM) e dal nome della tassa (T_NAME)
        # aggiungo al df8 le altre variabili di interesse
        #vatDf = vatDf.ix[vatDf['T_TAX']==True]
        #del vatDf['T_TAX']
        #del vatDf['AMOUNT']
        #df10 = pandas.merge(vatDf,df8,on=["M_NUM","T_NAME"])
        #recupero le variabili che servono e che sono associate alla move
        df9 = df1[['M_NUM','DATE','DATE_DOC','M_REF','PARTNER']]
        df9 = df9.drop_duplicates() 
        #recupero le variabili che servono e che sono associate al nome dell'imposte
        df10 = df1[['T_NAME','T_DET','T_CRED','T_IMM', 'T_EXI']]
        df10 = df10[df10['T_DET'].notnull()]
        df10 = df10.drop_duplicates() 
        #combino il df8 prima con i dati associati alla move e
        # quindi con i dati associati alla tassa
        df11 = pandas.merge(df8 , df9,on=["M_NUM"], how='left')
        df12 = pandas.merge(df11, df10,on=["T_NAME"], how='left')
        df12 = df12.sort(['DATE','M_NUM'])
        df13 = df12.reset_index(drop=True)
        df13 = df13[LVAR]
        #PMN = ""
        #for i in range(len(df10)):
        #    row = df10[i:i+1]
        #    MN = row['M_NUM'][i]
        #    if MN==PMN:
        #        df10[i:i+1]['DATE_DOC'] = ''
        #        df10[i:i+1]['DATE'] = ''
        #        df10[i:i+1]['M_NUM'] = ''
        #        df10[i:i+1]['PARTNER'] = ''
        #        df10[i:i+1]['M_REF'] = ''
        #    PMN = MN
        #aggiungo una variabile "ordinamento" per ogni move
        df13['ORDTOT']=range(len(df13))
        df14=df13.groupby(['M_NUM']).apply(GroupInterOrd)
        #isolo il DF con la prima riga della move
        df15=df14.ix[df14['ORD']==0]
        #isolo il DF con le altre righe della move
        #e poongo a "" le variabili che nondevono essere stampate
        df16=df14.ix[df14['ORD']>0]
        df16[['DATE_DOC','DATE','M_NUM','PARTNER','M_REF']] = ''
        #ricombino i due df
        df17=pandas.concat([df15,df16])
        df17=df17.sort('ORDTOT')
        df17=df17[LVAR]
        return df17
    else:
        return pandas.DataFrame(columns=['DATE','M_NUM','DATE_DOC','M_REF','PARTNER','T_NAME','BASE','TAX','T_CRED','T_DET','T_IMM','T_EXI'])


def getVatSummary(vatDf, companyName, onlyValidatedMoves, 
                    sequenceName=None, periodName=None, fiscalyearName=None):
    '''
    funzione per il calcolo dei riepiloghi iva
    @param vatDf: è il dataframe contenente le informazioni specifiche per i report iva
    @param onlyValidatedMoves: booleano che indica se filtrare solo le scritture validate oppure no
    
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
    '''
    LVAR=['TEXT','T_NAME','BASE_DEB','TAX_DEB','BASE_CRED','TAX_CRED','T_DET','T_IMM','TOTAL']
    
    df1 = getVatRegister(vatDf, companyName, onlyValidatedMoves, periodName=periodName, fiscalyearName=fiscalyearName, sequenceName=sequenceName)
    del df1['DATE']
    del df1['M_NUM']
    del df1['DATE_DOC']
    del df1['M_REF']
    del df1['PARTNER']
    del df1['T_EXI']
    #somma di imponibile e di imposta per ogni tassa
    df2 = df1.groupby(['T_NAME','T_CRED']).sum()[['BASE','TAX']].reset_index()
    #aggiutna colonne BASE_CRED, TAX_CRED, BASE_DEB, TAX_DEB con rispettivi valori a seconda di T_CRED
    df2['BASE_CRED'] = 0.0
    df2['TAX_CRED'] = 0.0
    df2['BASE_DEB'] = 0.0
    df2['TAX_DEB'] = 0.0
    df2['BASE_CRED'].ix[df2['T_CRED']==True] = df2['BASE']
    df2['TAX_CRED'].ix[df2['T_CRED']==True] = df2['TAX']
    df2['BASE_DEB'].ix[df2['T_CRED']==False] = df2['BASE']
    df2['TAX_DEB'].ix[df2['T_CRED']==False] = df2['TAX']
    del df2['BASE']
    del df2['TAX']
    del df2['T_CRED']
    #aggiunta di T_DET e T_IMM a df2
    del df1['BASE']
    del df1['TAX']
    del df1['T_CRED']
    df3 = df1.drop_duplicates()
    df4 = pandas.merge(df2,df3,on='T_NAME')
    #suddivisione in 3 dataframe
    dfImm = df4.ix[df4['T_IMM']==True]
    dfDiff = df4.ix[df4['T_IMM']==False]
    dfIndet = df4.ix[df4['T_DET']==False]
    #definizione funzione generica calcolo totale
    def getTotalRow(df,groupByCols):
        dfTotal = df.groupby(groupByCols).sum()[['BASE_CRED','TAX_CRED','BASE_DEB','TAX_DEB']].reset_index()
        dfTotal['TOTAL'] = True
        return dfTotal.reset_index(drop=True)
    #calcolo totali immediata + differita
    dfImmTotal = getTotalRow(dfImm,['T_IMM','T_DET'])
    dfDiffTotal = getTotalRow(dfDiff,['T_IMM','T_DET'])
    #calcolo totale detraibile
    dfDetTotal = pandas.concat([dfImmTotal,dfDiffTotal]).reset_index(drop=True)
    dfDetTotal = getTotalRow(dfDetTotal,['T_DET'])
    dfDetTotal['T_IMM'] = None
    dfDetTotal['TEXT'] = "TOTALE DETRAIBILE"
    #calcolo totale indetraibile
    dfIndetTotal = getTotalRow(dfIndet,['T_DET'])
    dfIndetTotal['T_IMM'] = None
    dfIndetTotal['TEXT'] = "TOTALE INDETRAIBILE"
    #calcolo totale detraib + indetraibile
    dfDetPlusIndetTotal = pandas.concat([dfDetTotal,dfIndetTotal]).reset_index(drop=True)
    dfDetPlusIndetTotal = getTotalRow(dfDetPlusIndetTotal,['TOTAL'])
    dfDetPlusIndetTotal['TEXT'] = "TOTALE DETR + INDETR"
    #costruzione dataframe finale
    row = {
        'TEXT' : ['IVA DETRAIBILE',],
        'T_NAME' : ['',],
        'BASE_DEB' : ['',],
        'TAX_DEB' : ['',],
        'BASE_CRED' : ['',],
        'TAX_CRED' : ['',],
        }
    dfResult = pandas.DataFrame(row)
    dfImmTotal['TEXT'] = "ad esigibilita' immediata"
    dfResult = pandas.concat([dfResult,dfImmTotal,dfImm]).reset_index(drop=True)
    dfDiffTotal['TEXT'] = "ad esigibilita' differita"
    dfResult = pandas.concat([dfResult,dfDiffTotal,dfDiff]).reset_index(drop=True)
    #aggiunta totale detraibile
    dfResult = pandas.concat([dfResult,dfDetTotal]).reset_index(drop=True)
    #aggiunta riga vuota
    emptyRow = row.copy()
    emptyRow['TEXT'] = ['',]
    dfR1 = pandas.DataFrame(emptyRow)
    dfResult = pandas.concat([dfResult,dfR1]).reset_index(drop=True)
    #aggiunta sezione indetraibile
    row['TEXT'] = ['IVA INDETRAIBILE',]
    dfR1 = pandas.DataFrame(row)
    dfResult = pandas.concat([dfResult,dfR1]).reset_index(drop=True)
    dfResult = pandas.concat([dfResult,dfIndet,dfIndetTotal]).reset_index(drop=True)
    #aggiunta riga vuota
    dfR1 = pandas.DataFrame(emptyRow)
    dfResult = pandas.concat([dfResult,dfR1]).reset_index(drop=True)
    #aggiunta totale detr + indetr
    dfResult = pandas.concat([dfResult,dfDetPlusIndetTotal]).reset_index(drop=True)
    
    dfResult['TEXT'].ix[dfResult['TEXT'].isnull()] = ""
    dfResult['T_NAME'].ix[dfResult['T_NAME'].isnull()] = ""
    dfResult = dfResult[LVAR]
    return dfResult

def getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, 
                        deferredVatCreditAccountCode, deferredVatDebitAccountCode, 
                        searchPayments=False, billsPeriodName=None, billsFiscalyearName=None, 
                        paymentsPeriodName=None, paymentsFiscalyearName=None):
    '''
    funzione che restituisce l'iva differita o da pagare per il periodo (o l'anno fiscale) passati come parametro
    se searchPayments è True, si stanno cercando le fatture che sono state pagate nel periodo(paymentsPeriodName) o anno fiscale(paymentsFiscalyearName) ed emesse nel periodo (billsPeriodName) o anno fiscale (billsFiscalyearName)
    se searchPayments è False, si stanno cercando le fatture che non sono state ancora pagate entro il periodo(paymentsPeriodName) o anno fiscale(paymentsFiscalyearName)
    @param searchPayments: boolean che indica se si stanno cercando le fatture pagate nel periodo "paymentsPeriodName" oppure quelle non pagate entro il periodo "paymentsPeriodName"
    @param paymentsPeriodName: indica il periodo relativo ai pagamenti
    @param paymentsFiscalyearName: indica l'anno fiscale relativo ai pagamenti
    @param billsPeriodName (opzionale): indica il periodo relativo all'emissione delle fatture. Considerato solo se searchPayments=True
    @param billsFiscalyearName (opzionale): indica l'anno fiscale relativo all'emissione delle fatture. Considerato solo se searchPayments=True
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
    '''
    if not paymentsPeriodName and not paymentsFiscalyearName:
        raise RuntimeError("Errore: i parametri paymentsPeriodName e paymentsFiscalyearName non devono essere entrambi nulli")
    companyPathPkl = os.path.join(picklesPath,companyName)
    starkTax = Stark.load(os.path.join(companyPathPkl,"TAX.pickle"))
    starkPeriod = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    dfPeriods = starkPeriod.DF
    starkMoveLine = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
    df0 = starkMoveLine.DF
    df1 = df0.ix[(df0['COD_CON']==deferredVatCreditAccountCode) | (df0['COD_CON']==deferredVatDebitAccountCode)]
    if onlyValidatedMoves:
        df1 = df1.ix[df0['STA_MOV']=='posted']
    df1['TAX_COD'].ix[df1['TAX_COD'].isnull()] = 'NULL'
    df1 = pandas.merge(df1,starkTax.DF,how='left',left_on='TAX_COD',right_on='TAX_CODE')
    for i in range(len(df1)):
        row = df1[i:i+1]
        moveName = row['M_NAME'][i]
        moveNameSplits = moveName.split("/")
        df1[i:i+1]['M_NAME'] = moveNameSplits[len(moveNameSplits)-1]
    del df1["ID0_MVL"]
    del df1["STA_MOV"]
    del df1["DATE_DOC"]
    del df1["CHK_MOV"]
    del df1["TAX_AMO"]
    del df1["TYP_JRN"]
    del df1["NAM_CON"]
    del df1["NAM_JRN"]
    del df1["NAM_MVL"]
    del df1["REF_MVL"]
    del df1["M_REF"]
    del df1["TAX_COD"]
    del df1["TAX_CODE"]
    del df1["BASE_CODE"]
    del df1["REF_TAX_CODE"]
    del df1["REF_BASE_CODE"]
    
    df2 = None
    if searchPayments:
        df2 = df1.ix[(df1['NAM_REC'].notnull()) | (df1['NAM_REC_P'].notnull())]
        dfWithPayments = None
        if paymentsPeriodName:
            dfWithPayments = df2.ix[df2['NAM_PRD']==paymentsPeriodName]
        else:
            dfWithPayments = df2.ix[df2['NAM_FY']==paymentsFiscalyearName]
        dfWithPayments = dfWithPayments.ix[
            ((dfWithPayments['COD_CON']==deferredVatCreditAccountCode) & (dfWithPayments['CRT_MVL']>0)) | 
            ((dfWithPayments['COD_CON']==deferredVatDebitAccountCode) & (dfWithPayments['DBT_MVL']>0))
            ]
        dfWithPayments['DBT_MVL']=dfWithPayments['DBT_MVL'].map(float)
        dfWithPayments['CRT_MVL']=dfWithPayments['CRT_MVL'].map(float)
        dfWithPayments['AMO'] = numpy.where(dfWithPayments['CRT_MVL'] > 0.0, dfWithPayments['CRT_MVL'], dfWithPayments['DBT_MVL'])
        dfWithPayments = dfWithPayments[['NAM_REC','NAM_REC_P','DATE','AMO']]
        dfWithPayments = dfWithPayments.rename(columns={'DATE' : 'DAT_PAY'})
        dfWithBills = df2.ix[
            ((df2['COD_CON']==deferredVatCreditAccountCode) & (df2['DBT_MVL']>0)) |
            ((df2['COD_CON']==deferredVatDebitAccountCode) & (df2['CRT_MVL']>0))
            ]
        if billsPeriodName:
            dfWithBills = dfWithBills.ix[dfWithBills['NAM_PRD']==billsPeriodName]
        elif billsFiscalyearName:
            dfWithBills = dfWithBills.ix[dfWithBills['NAM_FY']==billsFiscalyearName]
        dfWithBills['CREDIT'] = False
        dfWithBills['CREDIT'].ix[dfWithBills['DBT_MVL'] > 0] = True
        dfWithBills = dfWithBills[['DATE','NAM_PAR','NAM_TAX','M_NAME','NAM_SEQ','NAM_REC','NAM_REC_P','CREDIT']]
        dfWithBills['NAM_REC'].ix[dfWithBills['NAM_REC'].isnull()] = 'NULL'
        dfWithBills['NAM_REC_P'].ix[dfWithBills['NAM_REC_P'].isnull()] = 'NULL'
        df2 = pandas.merge(dfWithPayments,dfWithBills,on='NAM_REC')
        df3 = pandas.merge(dfWithPayments,dfWithBills,on='NAM_REC_P')
        df2 = pandas.concat([df2,df3])
        df2 = df2[['AMO','DATE','M_NAME','NAM_PAR','NAM_SEQ','NAM_TAX','CREDIT','DAT_PAY']]
    #else: si stanno cercando le fatture con esigibilità differita non ancora pagate
    else:
        dateStop = None
        if paymentsPeriodName:
            df10 = dfPeriods.ix[dfPeriods['NAM_PRD']==paymentsPeriodName]
            df10 = df10.reset_index()
            dateStop = df10['P_DAT_STOP'][0]
        else:
            df10 = dfPeriods.ix[dfPeriods['NAM_FY']==paymentsFiscalyearName]
            df10 = df10.reset_index()
            dateStop = df10[0:1]['FY_DAT_STOP'][0]
        #calcolo delle fatture ad esig. diff. non riconciliate e non parzialmente riconciliate entro il periodo d'interesse
        df2 = df1.ix[(df1['NAM_REC'].isnull()) & (df1['NAM_REC_P'].isnull()) & (df1['COD_SEQ']=='RIVA') & (df1['DATE'] <= dateStop)]
        df2.reset_index()
        #calcolo delle fatture ad esig. diff. totalmente riconciliate ma il cui pagamento è successivo al periodo d'interesse
        dfWithBills = df1.ix[((df1['NAM_REC'].notnull()) | (df1['NAM_REC_P'].notnull())) & (df1['COD_SEQ']=='RIVA') & (df1['DATE'] <= dateStop)]
        dfWithPayments = df1.ix[((df1['NAM_REC'].notnull()) | (df1['NAM_REC_P'].notnull())) & (df1['DATE'] <= dateStop)]        
        dfWithPayments = dfWithPayments.ix[
            ((dfWithPayments['COD_CON']==deferredVatCreditAccountCode) & (dfWithPayments['CRT_MVL']>0)) | 
            ((dfWithPayments['COD_CON']==deferredVatDebitAccountCode) & (dfWithPayments['DBT_MVL']>0))
            ]
        dfWithPayments['DBT_MVL']=dfWithPayments['DBT_MVL'].map(float)
        dfWithPayments['CRT_MVL']=dfWithPayments['CRT_MVL'].map(float)
        dfWithPayments['AMO_PAY'] = numpy.where(dfWithPayments['CRT_MVL'] > 0.0, dfWithPayments['CRT_MVL'], dfWithPayments['DBT_MVL'])
        dfWithPayments = dfWithPayments[['NAM_REC','NAM_REC_P','DATE','AMO_PAY']]
        dfWithPayments = dfWithPayments.rename(columns={'DATE' : 'DAT_PAY'})
        #aggiunta delle fatture senza pagamenti totali entro il periodo
        if len(dfWithBills)>0:
            if len(dfWithPayments)>0:
                df5 = dfWithPayments.ix[(dfWithPayments['NAM_REC'].notnull())]
                df4 = pandas.merge(dfWithBills,df5,on='NAM_REC',how='left')
                df4 = df4.ix[(df4['DAT_PAY'].isnull()) & (df4['NAM_REC'].notnull())]
                if len(df4)>0:
                    del df4['DAT_PAY']
                    df2 = pandas.concat([df2,df4])
                    df2 = df2.reset_index(drop=True)
            else:
                df2 = pandas.concat([df2,dfWithBills])
                df2 = df2.reset_index(drop=True)
        df2['DBT_MVL']=df2['DBT_MVL'].map(float)
        df2['CRT_MVL']=df2['CRT_MVL'].map(float)
        df2['AMO'] = numpy.where(df2['CRT_MVL'] > 0.0, df2['CRT_MVL'], df2['DBT_MVL'])
        #aggiunta delle fatture non totalmente pagate entro il periodo
        if len(dfWithPayments)>0:
            df5 = dfWithPayments.ix[(dfWithPayments['NAM_REC_P'].notnull())]
            df5 = df5.groupby('NAM_REC_P').sum()[['AMO_PAY']].reset_index()
            if len(dfWithBills)>0 and len(df5)>0:
                df4 = pandas.merge(dfWithBills,df5,on='NAM_REC_P')
                df4['DBT_MVL']=df4['DBT_MVL'].map(float)
                df4['CRT_MVL']=df4['CRT_MVL'].map(float)
                df4['AMO'] = numpy.where(df4['CRT_MVL'] > 0.0, df4['CRT_MVL']-df4['AMO_PAY'], df4['DBT_MVL']-df4['AMO_PAY'])
                df2 = pandas.concat([df2,df4])
                df2 = df2.reset_index(drop=True)
        #ultimi ritocchi
        df2['CREDIT'] = False
        df2['CREDIT'].ix[df2['DBT_MVL'] > 0] = True
        df2 = df2[['AMO','DATE','M_NAME','NAM_PAR','NAM_SEQ','NAM_TAX','CREDIT']]
    return df2.sort(['NAM_SEQ','DATE','M_NAME']).reset_index(drop=True)

def getDeferredVatSummary(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, 
                        deferredVatDebitAccountCode, billsPeriodName=None, billsFiscalyearName=None, 
                        paymentsPeriodName=None, paymentsFiscalyearName=None):
    '''
    funzione che restituisce il riepilogo dell'iva differita.
    Il periodo (o l'anno fiscale) deve essere passato come parametro
    @param paymentsPeriodName: indica il periodo relativo ai pagamenti
    @param paymentsFiscalyearName: indica l'anno fiscale relativo ai pagamenti
    @param billsPeriodName (opzionale): indica il periodo relativo all'emissione delle fatture. Considerato solo nella ricerca dei pagamenti
    @param billsFiscalyearName (opzionale): indica l'anno fiscale relativo all'emissione delle fatture. Considerato solo nella ricerca dei pagamenti
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
    '''
    if not paymentsPeriodName and not paymentsFiscalyearName:
        raise RuntimeError("Errore: i parametri paymentsPeriodName e paymentsFiscalyearName non devono essere entrambi nulli")
    payments = getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, 
                                deferredVatCreditAccountCode, deferredVatDebitAccountCode, 
                                searchPayments=True, paymentsPeriodName=paymentsPeriodName, 
                                paymentsFiscalyearName=paymentsFiscalyearName, 
                                billsPeriodName=billsPeriodName, billsFiscalyearName=billsFiscalyearName)
    notPayed = getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, 
                                deferredVatCreditAccountCode, deferredVatDebitAccountCode, 
                                searchPayments=False, paymentsPeriodName=paymentsPeriodName, 
                                paymentsFiscalyearName=paymentsFiscalyearName, 
                                billsPeriodName=billsPeriodName, billsFiscalyearName=billsFiscalyearName)
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
        
        def getTotalRow(df,searchPayments,credit,sequenceName=None):
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
            df2 = getTotalRow(df2,True,True,sequence)
            df2 = getTotalRow(df2,True,False,sequence)
            df2 = getTotalRow(df2,False,True,sequence)
            df2 = getTotalRow(df2,False,False,sequence)
        #aggiunta totali di sintesi
        df2 = getTotalRow(df2,True,True)
        df2 = getTotalRow(df2,True,False)
        df2 = getTotalRow(df2,False,True)
        df2 = getTotalRow(df2,False,False)
    return df2

def _appendLineToVatLiquidationDict(liqDict, text, namSeq, dbt, crt):
    liqDict['TEXT'].append(text)
    liqDict['NAM_SEQ'].append(namSeq)
    liqDict['DBT'].append(dbt)
    liqDict['CRT'].append(crt)

def addLiquidationSummaryFinalResults(moveLineDf, periodDf, debitVat, creditVat,
                                    companyName, onlyValidatedMoves, immediateVatCreditAccountCode, 
                                    immediateVatDebitAccountCode, deferredVatCreditAccountCode, 
                                    deferredVatDebitAccountCode, treasuryVatAccountCode, 
                                    periodName=None, fiscalyearName=None, liquidationDict=None):
    '''
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
    '''
    if not liquidationDict:
        liquidationDict = {
        'TEXT': [],
        'NAM_SEQ': [],
        'DBT': [],
        'CRT': [],
        }
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
        df0 = df0.ix[(df0['DATE']>=dateStart) & (df0['DATE']<=dateStop)]
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
    return liquidationDict

def getVatLiquidationSummary(picklesPath, companyName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode, periodName=None, fiscalyearName=None):
    '''
    funzione che restituisce il riepilogo di liquidazione iva
    Il periodo (o l'anno fiscale) deve essere passato come parametro
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
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
    starkMoveLine = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
    starkPeriod = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
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
        vatSummary = getVatSummary(picklesPath, companyName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, periodName=periodName, sequenceName=sequence)
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
    deferredSummary = getDeferredVatSummary(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, paymentsPeriodName=periodName, paymentsFiscalyearName=fiscalyearName)
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
    vatLiquidationDict = addLiquidationSummaryFinalResults(
                                        starkMoveLine.DF, starkPeriod.DF, debitVatTotal, 
                                        creditVatTotal, companyName, onlyValidatedMoves, 
                                        immediateVatCreditAccountCode, immediateVatDebitAccountCode, 
                                        deferredVatCreditAccountCode, deferredVatDebitAccountCode, 
                                        treasuryVatAccountCode, periodName=periodName, 
                                        fiscalyearName=fiscalyearName, liquidationDict=vatLiquidationDict)
    return pandas.DataFrame(vatLiquidationDict)
    
def getVatControlSummary(fiscalyearName, vatSummary, picklesPath, companyName, 
                        onlyValidatedMoves, immediateVatCreditAccountCode,
                        immediateVatDebitAccountCode, deferredVatCreditAccountCode, 
                        deferredVatDebitAccountCode, treasuryVatAccountCode):
    '''
    funzione che restituisce il df con il prospetto di controllo d'esercizio
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento
    T_NAME       nome dell'imposta
    T_ACC        codice del conto
    T_TAX        booleano che indica se è un'imposta (oppure un imponibile)
    T_CRED       booleano che indica se l'imposta è a credito
    T_DET        booleano che indica se l'imposta è detraibile
    T_IMM        booleano che indica se l'imposta è ad esigibilità immediata
    T_EXI        booleano che indica se l'imposta è esigibile nel periodo
    STATE       stato della scrittura contabile
    SEQUENCE    nome della sequenza
    PERIOD      periodo dell'esercizio
    JOURNAL     nome del journal
    DATE_DOC    data della fattura
    DATE        data di registrazione
    PARTNER     nome del partner
    RECON       nome della riconciliazione
    RECON_P     nome della riconciliazione parziale
    AMOUNT      importo (di imponibile o imposta o pagamento)
    '''
    #recupero iva immediata (a credito e a debito)
    #immediateCreditVat = 0
    #immediateDebitVat = 0
    #df0 = vatSummary.ix[(vatSummary['NAM_TAX']=='Totale') & (vatSummary['IMMED']==True) & (vatSummary['CREDIT']==True)].reset_index()
    #if len(df0)>0:
        #immediateCreditVat = df0[0:1]['TAX'][0]
    #df0 = vatSummary.ix[(vatSummary['NAM_TAX']=='Totale') & (vatSummary['IMMED']==True) & (vatSummary['CREDIT']==False)].reset_index()
    #if len(df0)>0:
        #immediateDebitVat = df0[0:1]['TAX'][0]
    ##recupero iva differita (a credito e a debito)
    #deferredCreditVat = 0
    #deferredDebitVat = 0
    #df0 = vatSummary.ix[(vatSummary['NAM_TAX']=='Totale') & (vatSummary['IMMED']==False) & (vatSummary['CREDIT']==True)].reset_index()
    #if len(df0)>0:
        #deferredCreditVat = df0[0:1]['TAX'][0]
    #df0 = vatSummary.ix[(vatSummary['NAM_TAX']=='Totale') & (vatSummary['IMMED']==False) & (vatSummary['CREDIT']==False)].reset_index()
    #if len(df0)>0:
        #deferredDebitVat = df0[0:1]['TAX'][0]
    ##calcolo iva differita divenuta esigibile dall'esercizio precedente
    #previousDeferredVatCredit = 0
    #previousDeferredVatDebit = 0
    #companyPathPkl = os.path.join(picklesPath,companyName)
    #dfMoveLines = Stark.load(os.path.join(companyPathPkl,"MVL.pickle")).DF
    #dfPeriods = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle")).DF
    #dfPeriods1 = dfPeriods[['FY_DAT_STR','NAM_FY']]
    #dfPeriods1 = dfPeriods1.drop_duplicates()
    #df0 = dfPeriods1.ix[dfPeriods1['NAM_FY']==fiscalyearName].reset_index()
    #fiscalyearDateStart = df0[0:1]['FY_DAT_STR'][0]
    #previousFiscalyearDateStart = date(fiscalyearDateStart.year-1,fiscalyearDateStart.month,fiscalyearDateStart.day)
    #df0 = dfPeriods1.ix[dfPeriods1['FY_DAT_STR']==previousFiscalyearDateStart].reset_index()
    #if len(df0) > 0:
        #previousFiscalyearName = df0[0:1]['NAM_FY'][0]
        #deferredSummary = getDeferredVatSummary(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode,  paymentsFiscalyearName=fiscalyearName, billsFiscalyearName=previousFiscalyearName)
        #df0 = deferredSummary.ix[(deferredSummary['NAM_SEQ']=='Sintesi') & 
                                #(deferredSummary['NAM_TAX']=='Totale') & 
                                #(deferredSummary['PAYM']==True) & 
                                #(deferredSummary['CREDIT']==True)].reset_index()
        #if len(df0) > 0:
            #previousDeferredVatCredit = df0[0:1]['AMO'][0]
        #df0 = deferredSummary.ix[(deferredSummary['NAM_SEQ']=='Sintesi') & 
                                #(deferredSummary['NAM_TAX']=='Totale') & 
                                #(deferredSummary['PAYM']==True) & 
                                #(deferredSummary['CREDIT']==False)].reset_index()
        #if len(df0) > 0:
            #previousDeferredVatDebit = df0[0:1]['AMO'][0]
    ##calcolo iva differita divenuta esigibile dall'esercizio corrente
    #currentDeferredVatCredit = 0
    #currentDeferredVatDebit = 0
    #deferredSummary = getDeferredVatSummary(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode,  paymentsFiscalyearName=fiscalyearName, billsFiscalyearName=fiscalyearName)
    #df0 = deferredSummary.ix[(deferredSummary['NAM_SEQ']=='Sintesi') & 
                            #(deferredSummary['NAM_TAX']=='Totale') & 
                            #(deferredSummary['PAYM']==True) & 
                            #(deferredSummary['CREDIT']==True)].reset_index()
    #if len(df0) > 0:
        #currentDeferredVatCredit = df0[0:1]['AMO'][0]
    #df0 = deferredSummary.ix[(deferredSummary['NAM_SEQ']=='Sintesi') & 
                            #(deferredSummary['NAM_TAX']=='Totale') & 
                            #(deferredSummary['PAYM']==True) & 
                            #(deferredSummary['CREDIT']==False)].reset_index()
    #if len(df0) > 0:
        #currentDeferredVatDebit = df0[0:1]['AMO'][0]
    ##calcolo totali
    #creditDeferredVatNowExigible = currentDeferredVatCredit + previousDeferredVatCredit
    #debitDeferredVatNowExigible = currentDeferredVatDebit + previousDeferredVatDebit
    #creditTotalVatExigible = creditDeferredVatNowExigible + immediateCreditVat
    #debitTotalVatExigible = debitDeferredVatNowExigible + immediateDebitVat
    #creditDeferredVatExigibleInNextExercise = deferredCreditVat - currentDeferredVatCredit
    #debitDeferredVatExigibleInNextExercise = deferredDebitVat - currentDeferredVatDebit
    ##aggiunta righe finali
    #print addLiquidationSummaryFinalResults(dfMoveLines, dfPeriods, immediateDebitVat + debitDeferredVatNowExigible, 
                                        #immediateCreditVat + creditDeferredVatNowExigible, companyName, onlyValidatedMoves, 
                                        #immediateVatCreditAccountCode, immediateVatDebitAccountCode, 
                                        #deferredVatCreditAccountCode, deferredVatDebitAccountCode, 
                                        #treasuryVatAccountCode, fiscalyearName=fiscalyearName)
    ##terminare il calcolo con la costruzione di un df appropriato
    #xxx
    #return 0
            
