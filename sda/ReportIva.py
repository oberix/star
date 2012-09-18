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
        
lm_riepiloghi_iva = {
        'TEXT': [0, '2c', "@v1","@v2",],
        'T_NAME': [1, '2c', "@v1","Tipo imposta"],
        'BASE_DEB': [2, '0.5r', 'Iva a debito',"Imponibile"],
        'TAX_DEB': [3, '0.5r', 'Iva a debito',"Imposta"],
        'BASE_CRED': [4, '0.5r', 'Iva a credito',"Imponibile "],
        'TAX_CRED': [5, '0.5r', 'Iva a credito',"Imposta "],
        }
        
lm_pagamenti_iva_differita = {
        'DAT_PAY': [0, 'c', 'Data incasso',"o pagamento"],
        'SEQUENCE': [1, '1.5c', 'Registro IVA',"@v1"],
        'M_NUM': [2, 'c', "Numero","protocollo"],
        'DATE': [3, 'c', "Data", "registrazione"],
        'PARTNER': [4, 'c', 'Controparte',"@v2"],
        'T_NAME': [5, '2c', 'Tipo',"imposta"],
        'AMOUNT': [6, '0.5r', 'Imposta',"@v3"],
        }
        
lm_da_pagare_iva_differita = {
        'SEQUENCE': [0, '1.5c', 'Registro IVA',"@v1"],
        'M_NUM': [1, 'c', 'Numero', 'protocollo'],
        'DATE': [2, 'c', 'Data', 'registrazione'],
        'PARTNER': [3, 'c', 'Controparte',"@v2"],
        'T_NAME': [4, '2c', 'Tipo', 'imposta'],
        'AMOUNT': [5, '0.5r', 'Imposta',"@v3"],
        }
        
lm_riepilogo_differita = {
        'T_NAME': [0, '2.5l', "@v1"],
        'TEXT': [1, 'l', "@v2"],
        'AMOUNT': [2, '0.5r', 'Imposta'],
        }
        
lm_liquidazione_iva = {
        'TEXT': [0, '2l', "@v1"],
        'SEQUENCE': [1, 'l', "@v2"],
        'DBT': [2, '0.5r', 'Iva a debito'],
        'CRT': [3, '0.5r', 'Iva a credito'],
        }
        
lm_controllo_esercizio = {
        'TEXT': [0, '4l', "@v1"],
        'DBT': [1, '0.5r', 'Iva a debito'],
        'CRT': [2, '0.5r', 'Iva a credito'],
        }


import sys
import os
import getopt
import pandas
import numpy
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
    configFilePath = os.path.join(BASEPATH,"config","report_iva.cfg")
    config = Config(configFilePath)
    config.parse()
    #assegna ai parametri di interesse il valore letto in config
    comNam=config.options.get('company',False)
    picklesPath = config.options.get('pickles_path',False)
    reportType=int(config.options.get('report_type',False))
    fiscalyearName=config.options.get('fiscalyear',False)
    periodName=config.options.get('period',False)
    sequenceName=config.options.get('sequence',False)
    treasuryVatAccountCode=config.options.get('treasury_vat_account_code',False)
    #verifica che la stringa associata al parametro only_validated_moves inserita in config
    #sia effettivamente un valore boleano 
    onlyValML=True
    if str(config.options.get('only_validated_moves',True))=='False':
        onlyValML=False
    #lettura degli oggetti stark di interesse
    companyPathPkl = os.path.join(picklesPath,comNam)
    vatStarK = Stark.load(os.path.join(companyPathPkl,"VAT.pickle"))
    vatDf = vatStarK.DF
    periodStarK = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    periodDf = periodStarK.DF
    companyStarK = Stark.load(os.path.join(companyPathPkl,"COMP.pickle"))
    companyDf = companyStarK.DF
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    #in  base al tipo di report scelto dall'utente, il programma lancia la funzione corrispondente
    try:
        #vat registers
        if reportType==1:
            vatRegister = getVatRegister(vatDf, comNam, onlyValML, fiscalyearName=fiscalyearName, sequenceName=sequenceName)
            bagVatRegister = Bag(vatRegister, os.path.join(OUT_PATH, 'vat_register.pickle'), 
                                 TI='tab',LM=lm_registri_iva)
            setattr(bagVatRegister,"SEQUENCE",sequenceName)
            setattr(bagVatRegister,"YEAR",fiscalyearName)
            setattr(bagVatRegister,"COMPANY_STRING",companyString)
            OUT_PATH = os.path.join(SRE_PATH, 'registro_iva')
            bagVatRegister.save()
        #vat summary
        elif reportType==2:
            vatSummary = getVatSummary(vatDf, comNam, onlyValML,
                                       periodName=periodName, sequenceName=sequenceName)
            bagVatSummary = Bag(vatSummary,os.path.join(OUT_PATH, 'vat_summary.pickle'), 
                                TI='tab',LM=lm_riepiloghi_iva)
            setattr(bagVatSummary,"SEQUENCE",sequenceName)
            setattr(bagVatSummary,"PERIOD",periodName)
            setattr(bagVatSummary,"COMPANY_STRING",companyString)
            OUT_PATH = os.path.join(SRE_PATH, 'riepilogo_iva')
            bagVatSummary.save()
        #vat detail
        elif reportType==3:
            vatRegister = getVatRegister(vatDf, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            bagVatRegister = Bag(vatRegister, os.path.join(OUT_PATH, 'vat_register.pickle'),
                                 TI='tab', LM=lm_registri_iva)
            setattr(bagVatRegister,"SEQUENCE",sequenceName)
            setattr(bagVatRegister,"PERIOD",periodName)
            setattr(bagVatRegister,"COMPANY_STRING",companyString)
            vatSummary=getVatSummary(vatDf, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            bagVatSummary = Bag(vatSummary, os.path.join(OUT_PATH, 'vat_summary.pickle'),
                                TI='tab',LM=lm_riepiloghi_iva,TITLE='Riepilogo')
            OUT_PATH = os.path.join(SRE_PATH, 'dettaglio_iva')
            bagVatRegister.save()
            bagVatSummary.save()
        #deferred vat detail
        elif reportType==4:            
            payments = getDeferredVatDetailPayments(vatDf, comNam, onlyValML, paymentsPeriodName=periodName)
            notPayed = getDeferredVatDetailNotPayed(vatDf, comNam, onlyValML, periodDf, paymentsPeriodName=periodName)
            bagPayments = Bag(payments, os.path.join(OUT_PATH, 'payments.pickle'),
                              TI='tab', LM=lm_pagamenti_iva_differita)
            setattr(bagPayments,"PERIOD",periodName)
            setattr(bagPayments,"COMPANY_STRING",companyString)
            bagNotPayed = Bag(notPayed, os.path.join(OUT_PATH, 'not_payed.pickle'),
                              TI='tab',LM=lm_da_pagare_iva_differita)
            OUT_PATH = os.path.join(SRE_PATH, 'dettaglio_iva_differita')
            bagPayments.save()
            bagNotPayed.save()
        #deferred vat summary
        elif reportType==5:
            deferredVatSummaryDf = getDeferredVatSummary(vatDf, comNam, onlyValML, 
                                                            periodDf, paymentsPeriodName=periodName)
            bagSummary= Bag(deferredVatSummaryDf['dfSummary'], 
                            os.path.join(OUT_PATH, 'deferred_vat_summary.pickle'),
                            TI='tab',LM=lm_riepilogo_differita,TITLE="Riepilogo")
            setattr(bagSummary,"PERIOD",periodName)
            setattr(bagSummary,"COMPANY_STRING",companyString)
            bagSynthesis= Bag(deferredVatSummaryDf['dfSynthesis'],
                              os.path.join(OUT_PATH, 'deferred_vat_synthesis.pickle'),
                              TI='tab',LM=lm_riepilogo_differita,TITLE="Sintesi")
            OUT_PATH = os.path.join(SRE_PATH, 'riepilogo_iva_differita')
            bagSummary.save()
            bagSynthesis.save()
        #vat liquidation
        elif reportType==6:
            liquidationSummary = getVatLiquidationSummary(vatDf, periodDf,
                                                                comNam, onlyValML, treasuryVatAccountCode, periodName=periodName)
            bagLiquidationSummary = Bag(liquidationSummary, 
                                        os.path.join(OUT_PATH, 'liquidation_summary.pickle'),
                                        TI='tab',LM=lm_liquidazione_iva,TITLE='Prospetto liquidazione Iva')
            setattr(bagLiquidationSummary,"PERIOD",periodName)
            setattr(bagLiquidationSummary,"COMPANY_STRING",companyString)
            OUT_PATH = os.path.join(SRE_PATH, 'liquidazione_iva')
            bagLiquidationSummary.save()
        #exercise control summary
        elif reportType==7:
            vatSummary = getVatSummary(vatDf, comNam, onlyValML, fiscalyearName=fiscalyearName)
            vatControlSummaryDf = getVatControlSummary(fiscalyearName, vatSummary, vatDf, 
                                                            periodDf, comNam, onlyValML, treasuryVatAccountCode)
            OUT_PATH = os.path.join(SRE_PATH, 'controllo_esercizio')
            bagVatSummary = Bag(vatSummary,
                                os.path.join(OUT_PATH, 'vat_summary.pickle'),
                                TI='tab',LM=lm_riepiloghi_iva,TITLE='Riepilogo IVA')
            setattr(bagVatSummary,"YEAR",fiscalyearName)
            setattr(bagVatSummary,"COMPANY_STRING",companyString)
            bagVatSummary.save()
            bagSummary2 = Bag(vatControlSummaryDf['summary'],
                              os.path.join(OUT_PATH, 'vat_summary_2.pickle'),
                              TI='tab',LM=lm_controllo_esercizio,TITLE='Riepilogo con IVA diventata esigibile')
            bagSummary2.save()
            bagLiquidationSummary = Bag(vatControlSummaryDf['liquidationSummary'],
                                        os.path.join(OUT_PATH, 'liquidation_summary.pickle'),
                                        TI='tab',LM=lm_controllo_esercizio,TITLE='Liquidazione IVA')
            bagLiquidationSummary.save()
    except:
        raise

    return 0


###########
#### funzioni di calcolo dei report
###########

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
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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

    #filtro solo le voci di giornale che provengono da una fattura
    df0 = vatDf.ix[(vatDf['DATE_DOC'].notnull())]
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
        df6 = df1.sort(['DATE','M_NAME']).reset_index(drop=True)
        #pulisco il database di eventuali casi in cui ho all'interno di una scrittura
        #più linee riguardanti la stessa imposta
        #calcolo la somma per ogni move delle imposte e dell'imponibile per ciascuna tassa
        G001 = ['M_NAME','T_NAME','T_TAX']
        df7 = df6.groupby(G001).sum()[['AMOUNT']].reset_index()
        df7['AMOUNT']=df7['AMOUNT'].map(float)
        #fine pulizie
        #isolo le imposte dalla base imponibile e tiporto le due variabili in colonna
        df7['ST_TAX'] = 'TAX'
        df7['ST_TAX'].ix[df7['T_TAX']==False] = 'BASE'
        #aggiunta colonne BASE e TAX con importi di imponibile e imposta a seconda delle righe
        df8 = pandas.pivot_table(df7,values='AMOUNT', cols=['ST_TAX'], 
                        rows=['M_NAME','T_NAME'])
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
        df9 = df1[['M_NUM','DATE','DATE_DOC','M_REF','PARTNER','M_NAME']]
        df9 = df9.drop_duplicates() 
        #recupero le variabili che servono e che sono associate al nome dell'imposte
        df10 = df1[['T_NAME','T_DET','T_CRED','T_IMM', 'T_EXI']]
        df10 = df10[df10['T_DET'].notnull()]
        df10 = df10.drop_duplicates() 
        #combino il df8 prima con i dati associati alla move e
        # quindi con i dati associati alla tassa
        df11 = pandas.merge(df8 , df9,on=["M_NAME"], how='left')
        df12 = pandas.merge(df11, df10,on=["T_NAME"], how='left')
        df12 = df12.sort(['DATE','M_NAME'])
        df13 = df12.reset_index(drop=True)
        df13 = df13[['DATE','M_NUM','DATE_DOC','M_REF','PARTNER','T_NAME','BASE','TAX','T_CRED','T_DET','T_IMM','T_EXI','M_NAME']]
        #PMN = ""
        #for i in range(len(df13)):
        #    row = df13[i:i+1]
        #    MN = row['M_NUM'][i]
        #    if MN==PMN:
        #        df13[i:i+1]['DATE_DOC'] = ''
        #        df13[i:i+1]['DATE'] = ''
        #        df13[i:i+1]['M_NUM'] = ''
        #        df13[i:i+1]['PARTNER'] = ''
        #        df13[i:i+1]['M_REF'] = ''
        #    PMN = MN
        #aggiungo una variabile "ordinamento" per ogni move
        df13['ORDTOT']=range(len(df13))
        df14=df13.groupby(['M_NAME']).apply(GroupInterOrd)
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
        return pandas.DataFrame(columns=LVAR)


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
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
    df2['BASE_CRED'] = numpy.where(df2['T_CRED']==True,df2['BASE'],0)
    df2['TAX_CRED'] = numpy.where(df2['T_CRED']==True,df2['TAX'],0)
    df2['BASE_DEB'] = numpy.where(df2['T_CRED']==False,df2['BASE'],0)
    df2['TAX_DEB'] = numpy.where(df2['T_CRED']==False,df2['TAX'],0)
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

def getDeferredVatDetailPayments(vatDf, companyName, onlyValidatedMoves, 
                        billsPeriodName=None, billsFiscalyearName=None, 
                        paymentsPeriodName=None, paymentsFiscalyearName=None):
    '''
    funzione che restituisce l'iva differita pagata nel il periodo (o l'anno fiscale) passati come parametro
    @param paymentsPeriodName: filtra i pagamenti per il periodo indicato
    @param paymentsFiscalyearName: filtra i pagamenti per l'anno fiscale indicato
    @param billsPeriodName: filtra le fatture per periodo di emissione
    @param billsFiscalyearName: filtra le fatture per anno fiscale di emissione
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
    if onlyValidatedMoves:
        vatDf = vatDf.ix[vatDf["STATE"]=='posted']
    df2 = vatDf.ix[(vatDf['RECON'].notnull()) | (vatDf['RECON_P'].notnull())]
    dfWithPayments = df2.ix[df2['CASH']==True]
    dfWithBills = df2.ix[df2['CASH']==False]
    if len(dfWithPayments)>0:
        if paymentsPeriodName:
            dfWithPayments = dfWithPayments.ix[df2['PERIOD']==paymentsPeriodName]
        else:
            dfWithPayments = dfWithPayments.ix[df2['ESER']==paymentsFiscalyearName]
    if len(dfWithBills)>0:
        if billsPeriodName:
            dfWithBills = dfWithBills.ix[dfWithBills['PERIOD']==billsPeriodName]
        elif billsFiscalyearName:
            dfWithBills = dfWithBills.ix[dfWithBills['ESER']==billsFiscalyearName]
    if len(dfWithPayments)>0 and len(dfWithBills)>0:
        dfWithPayments['AMOUNT']=dfWithPayments['AMOUNT'].map(float)
        dfWithPayments = dfWithPayments[['RECON','RECON_P','DATE','AMOUNT']]
        dfWithPayments = dfWithPayments.rename(columns={'DATE' : 'DAT_PAY'})
        dfWithBills['RECON'].ix[dfWithBills['RECON'].isnull()] = 'NULL'
        dfWithBills['RECON_P'].ix[dfWithBills['RECON_P'].isnull()] = 'NULL'
        dfWithBills = dfWithBills[['DATE','PARTNER','T_NAME','M_NUM','SEQUENCE','RECON','RECON_P','T_CRED']]
        df2 = pandas.merge(dfWithPayments,dfWithBills,on='RECON')
        df3 = pandas.merge(dfWithPayments,dfWithBills,on='RECON_P')
        df2 = pandas.concat([df2,df3])
        df2 = df2[['AMOUNT','DATE','M_NUM','PARTNER','SEQUENCE','T_NAME','T_CRED','DAT_PAY']]
        return df2
    else:
        return pandas.DataFrame(columns=['AMOUNT','DATE','M_NUM','PARTNER','SEQUENCE','T_NAME','T_CRED','DAT_PAY'])

def getDeferredVatDetailNotPayed(vatDf, companyName, onlyValidatedMoves, periodDf,
                        paymentsPeriodName=None, paymentsFiscalyearName=None):
    '''
    funzione che restituisce l'iva differita non ancora pagata entro il periodo (o l'anno fiscale) passati come parametro
    @param paymentsPeriodName: filtra i pagamenti entro il periodo indicato
    @param paymentsFiscalyearName: filtra i pagamenti entro l'anno fiscale indicato
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
    dateStop = None
    if paymentsPeriodName:
        df10 = periodDf.ix[periodDf['NAM_PRD']==paymentsPeriodName]
        df10 = df10.reset_index()
        dateStop = df10['P_DATE_STOP'][0]
    else:
        df10 = periodDf.ix[periodDf['NAM_FY']==paymentsFiscalyearName]
        df10 = df10.reset_index()
        dateStop = df10[0:1]['FY_DATE_STOP'][0]
    if onlyValidatedMoves:
        vatDf = vatDf.ix[vatDf["STATE"]=='posted']
    #calcolo delle fatture ad esig. diff. non riconciliate e non parzialmente riconciliate entro il periodo d'interesse
    df2 = vatDf.ix[(vatDf['RECON'].isnull()) & (vatDf['RECON_P'].isnull()) & (vatDf['DATE'] <= dateStop) & (vatDf['CASH']==False)]
    df2.reset_index()
    #calcolo fatture parzialmente (o totalmente) pagate
    df3 = vatDf.ix[((vatDf['RECON'].notnull()) | (vatDf['RECON_P'].notnull())) & (vatDf['DATE'] <= dateStop)]
    dfWithBills = df3.ix[df3['CASH']==False]
    #calcolo pagamenti effettuati entro il periodo
    dfWithPayments = df3.ix[df3['CASH']==True]
    dfWithPayments['AMOUNT']=dfWithPayments['AMOUNT'].map(float)
    dfWithPayments = dfWithPayments[['RECON','RECON_P','DATE','AMOUNT']]
    dfWithPayments = dfWithPayments.rename(columns={'DATE' : 'DAT_PAY'})
    #calcolo delle fatture non pagate entro il periodo
    if len(dfWithBills)>0:
        if len(dfWithPayments)>0:
            df4 = dfWithPayments.copy()
            del df4['AMOUNT']
            #df5 = fatture totalmente pagate
            df5 = dfWithBills.ix[dfWithBills['RECON'].notnull()]
            df6 = pandas.DataFrame()
            if len(df5)>0:
                df6 = pandas.merge(df5,df4,on='RECON',how='left')
                df6 = df6.ix[df6['DAT_PAY'].isnull()]
            #df7 = fatture parzialmente pagate
            df7 = dfWithBills.ix[dfWithBills['RECON_P'].notnull()]
            df8 = pandas.DataFrame()
            if len(df7)>0:
                df8 = pandas.merge(df7,df4,on='RECON_P',how='left')
                df8 = df8.ix[df8['DAT_PAY'].isnull()]
            df9 = pandas.concat([df6,df8])
            if len(df9)>0:
                del df9['DAT_PAY']
                df2 = pandas.concat([df2,df9])
                df2 = df2.reset_index(drop=True)
        else:
            df2 = pandas.concat([df2,dfWithBills])
            df2 = df2.reset_index(drop=True)
    #calcolo del residuo delle fatture parzialmente riconciliate entro il periodo
    if len(dfWithPayments)>0:
        df5 = dfWithPayments.ix[(dfWithPayments['RECON_P'].notnull())]
        df5 = df5.groupby('RECON_P').sum()[['AMOUNT']].reset_index()
        df5 = df5.rename(columns={'AMOUNT' : 'AMO_PAY'})
        if len(dfWithBills)>0 and len(df5)>0:
            df4 = pandas.merge(dfWithBills,df5,on='RECON_P')
            df4['AMOUNT'] = df4['AMOUNT'] - df4['AMO_PAY']
            df2 = pandas.concat([df2,df4])
            df2 = df2.reset_index(drop=True)
    df2 = df2[['AMOUNT','DATE','M_NUM','PARTNER','SEQUENCE','T_NAME','T_CRED']]
    df2 = df2.sort(['SEQUENCE','DATE','M_NUM']).reset_index(drop=True)
    return df2

def getDeferredVatSummary(vatDf, companyName, onlyValidatedMoves, periodDf,
                        billsPeriodName=None, billsFiscalyearName=None, 
                        paymentsPeriodName=None, paymentsFiscalyearName=None):
    '''
    funzione che restituisce il riepilogo dell'iva differita.
    Il periodo (o l'anno fiscale) dei pagamenti deve essere passato come parametro
    @param paymentsPeriodName: filtra i pagamenti per il periodo indicato
    @param paymentsFiscalyearName: filtra i pagamenti per l'anno fiscale indicato
    @param billsPeriodName: filtra le fatture per periodo di emissione
    @param billsFiscalyearName: filtra le fatture per anno fiscale di emissione
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
    payments = getDeferredVatDetailPayments(vatDf, companyName, onlyValidatedMoves, 
                                paymentsPeriodName=paymentsPeriodName, paymentsFiscalyearName=paymentsFiscalyearName, 
                                billsPeriodName=billsPeriodName, billsFiscalyearName=billsFiscalyearName)
    notPayed = getDeferredVatDetailNotPayed(vatDf, companyName, onlyValidatedMoves, periodDf,
                                paymentsPeriodName=paymentsPeriodName, paymentsFiscalyearName=paymentsFiscalyearName)
    payments = payments[['AMOUNT','T_NAME','SEQUENCE','T_CRED']]
    notPayed = notPayed[['AMOUNT','T_NAME','SEQUENCE','T_CRED']]
    payments['PAYM'] = True
    notPayed['PAYM'] = False
    
    dfToPrint1 = pandas.DataFrame(columns=['T_NAME','TEXT','AMOUNT','T_CRED','PAYM'])
    dfToPrint2 = pandas.DataFrame()
    
    def getTotalRow(dataDf,payments,credit,tName=False):
        '''
        funzione che restituisce un dataframe con una riga di totale dei dataframe di stampa
        @param payments: booleano che indica se la riga è per un totale 'incassata o pagata' (=True) o 'da incassare o pagare' (=False)
        @param credit: booleano che indica se è iva a credito(=True) o a debito(=False)
        @param tName: booleano che se = True provoca il filtraggio di dataDf per le righe che hanno la colonna T_NAME='Totale'
        '''
        df1 = dataDf.ix[(dataDf['PAYM']==payments) & (dataDf['T_CRED']==credit)].reset_index()
        if tName:
            df1 = df1.ix[df1['T_NAME']=='Totale'].reset_index()
        amount = 0
        if len(df1)>0:
            amount = df1['AMOUNT'][0]
        text = (credit) and 'a credito' or 'a debito'
        df2 = pandas.DataFrame({
                            'TEXT':[text,],
                            'AMOUNT':[amount,],
                            'T_CRED': [credit,],
                            'PAYM': [payments,],
                            })
        return df2
    
    ###
    #costruzione dataframe di riepilogo
    ###
    df1 = pandas.concat([payments,notPayed])
    df1 = df1.reset_index(drop=True)
    df1 = df1.sort(['SEQUENCE'])
    if len(df1) > 0:
        df2 = df1.groupby(['T_NAME','PAYM','T_CRED','SEQUENCE']).sum()[['AMOUNT']].reset_index()
        df2 = df2.sort(['SEQUENCE'])
        df3 = df2[['SEQUENCE']]
        df3 = df3.drop_duplicates()
        sequences = list(df3['SEQUENCE'])
        
        def computeTotalRow(df,searchPayments,credit,sequenceName=None):
            '''
            funzione per il calcolo dei totali del dataframe con i dati di riepilogo
            '''
            tempDf = df.ix[(df['PAYM']==searchPayments) & (df['T_CRED']==credit)]
            if sequenceName:
                tempDf = tempDf.ix[tempDf['SEQUENCE']==sequenceName]
            else:
                tempDf = tempDf.ix[tempDf['T_NAME']=='Totale']
                tempDf['SEQUENCE'] = 'Sintesi'
            del tempDf['T_NAME']
            if len(tempDf)>0:
                tempDf = tempDf.groupby(['PAYM','T_CRED','SEQUENCE']).sum()[['AMOUNT']].reset_index()
                tempDf['T_NAME'] = "Totale"
                return tempDf.reset_index(drop=True)
            else:
                return pandas.DataFrame()
        #aggiunta totali per ogni sequenza    
        for sequence in sequences:
            df3 = computeTotalRow(df2,True,True,sequence)
            df4 = computeTotalRow(df2,True,False,sequence)
            df5 = computeTotalRow(df2,False,True,sequence)
            df6 = computeTotalRow(df2,False,False,sequence)
            df2 = pandas.concat([df2,df3,df4,df5,df6]).reset_index(drop=True)
        #aggiunta totali di sintesi
        df3 = computeTotalRow(df2,True,True)
        df4 = computeTotalRow(df2,True,False)
        df5 = computeTotalRow(df2,False,True)
        df6 = computeTotalRow(df2,False,False)
        dfFinal = pandas.concat([df2,df3,df4,df5,df6]).reset_index(drop=True)
        #creazione df per la stampa
        for sequence in sequences:
            df1 = pandas.DataFrame({'T_NAME':[sequence,]})
            dfToPrint1 = pandas.concat([dfToPrint1,df1]).reset_index(drop=True)
            df2 = dfFinal.ix[dfFinal['SEQUENCE']==sequence]
            df3 = df2.ix[df2['T_NAME']!='Totale']
            df3 = df3.groupby('T_NAME')
            #aggiunta righe per tasse
            for group in df3:
                df4 = pandas.DataFrame({'T_NAME':[group[0],]})
                dfToPrint1 = pandas.concat([dfToPrint1,df4]).reset_index(drop=True)
                df5 = group[1]
                #aggiunta riga 'incassata o pagata'
                df6 = df5.ix[df5['PAYM']==True].reset_index()
                amount = 0
                if len(df6)>0:
                    amount = df6['AMOUNT'][0]
                df7 = pandas.DataFrame({
                                    'TEXT':['incassata o pagata',],
                                    'AMOUNT':[amount,],
                                    })
                dfToPrint1 = pandas.concat([dfToPrint1,df7]).reset_index(drop=True)
                #aggiunta riga 'da incassare o pagare'
                df8 = df5.ix[df5['PAYM']==False].reset_index()
                amount = 0
                if len(df8)>0:
                    amount = df8['AMOUNT'][0]
                df9 = pandas.DataFrame({
                                    'TEXT':['da incassare o pagare',],
                                    'AMOUNT':[amount,],
                                    })
                dfToPrint1 = pandas.concat([dfToPrint1,df9]).reset_index(drop=True)
            
            ###
            #aggiunta righe 'totale incassata o pagata'
            ###
            df9 = pandas.DataFrame({'T_NAME':['Totale IVA incassata o pagata',],})
            dfToPrint1 = pandas.concat([dfToPrint1,df9]).reset_index(drop=True)
            #aggiungo riga totale a debito
            df10 = getTotalRow(df2,True,False,True)
            dfToPrint1 = pandas.concat([dfToPrint1,df10]).reset_index(drop=True)
            #aggiungo riga totale a credito
            df10 = getTotalRow(df2,True,True,True)
            dfToPrint1 = pandas.concat([dfToPrint1,df10]).reset_index(drop=True)
            
            ###
            #aggiunta righe 'totale da incassare o pagare'
            ###
            df9 = pandas.DataFrame({'T_NAME':['Totale IVA da incassare o pagare',],})
            dfToPrint1 = pandas.concat([dfToPrint1,df9]).reset_index(drop=True)
            #aggiungo riga totale a debito
            df10 = getTotalRow(df2,False,False,True)
            dfToPrint1 = pandas.concat([dfToPrint1,df10]).reset_index(drop=True)
            #aggiungo riga totale a credito
            df10 = getTotalRow(df2,False,True,True)
            dfToPrint1 = pandas.concat([dfToPrint1,df10]).reset_index(drop=True)
            
            ###aggiunta riga vuota
            df11 = pandas.DataFrame({'T_NAME':['',]})
            dfToPrint1 = pandas.concat([dfToPrint1,df11]).reset_index(drop=True)
    
    ###
    #costruzione dataframe di sintesi
    ###
    df2 = dfToPrint1[['AMOUNT','T_CRED','PAYM']]
    df3 = df2.ix[(df2['T_CRED'].notnull()) & (df2['PAYM'].notnull())]
    df4 = df3.groupby(['T_CRED','PAYM']).sum()[['AMOUNT']].reset_index()
    #aggiunta righe 'totale incassata o pagata'
    df9 = pandas.DataFrame({'T_NAME':['Totale IVA incassata o pagata',],})
    dfToPrint2 = pandas.concat([dfToPrint2,df9]).reset_index(drop=True)
    #aggiungo riga totale a debito
    df10 = getTotalRow(df4,True,False)
    dfToPrint2 = pandas.concat([dfToPrint2,df10]).reset_index(drop=True)
    #aggiungo riga totale a credito
    df10 = getTotalRow(df4,True,True)
    dfToPrint2 = pandas.concat([dfToPrint2,df10]).reset_index(drop=True)
    #aggiunta righe 'totale da incassare o pagare'
    df9 = pandas.DataFrame({'T_NAME':['Totale IVA da incassare o pagare',],})
    dfToPrint2 = pandas.concat([dfToPrint2,df9]).reset_index(drop=True)
    #aggiungo riga totale a debito
    df10 = getTotalRow(df4,False,False)
    dfToPrint2 = pandas.concat([dfToPrint2,df10]).reset_index(drop=True)
    #aggiungo riga totale a credito
    df10 = getTotalRow(df4,False,True)
    dfToPrint2 = pandas.concat([dfToPrint2,df10]).reset_index(drop=True)
    
    ###
    #ultime formattazioni
    ###
    if len(dfToPrint1)>0:
        dfToPrint1['PAYM']=dfToPrint1['PAYM'].map(str)
        dfToPrint1['T_CRED']=dfToPrint1['T_CRED'].map(str)
        dfToPrint1['T_NAME'].ix[dfToPrint1['T_NAME'].isnull()] = ''
        dfToPrint1['TEXT'].ix[dfToPrint1['TEXT'].isnull()] = ''
        dfToPrint1['PAYM'].ix[dfToPrint1['PAYM'].isnull()] = ''
        dfToPrint1['T_CRED'].ix[dfToPrint1['T_CRED'].isnull()] = ''
        dfToPrint1['AMOUNT'].ix[dfToPrint1['AMOUNT'].isnull()] = -1
        dfToPrint1['AMOUNT']=dfToPrint1['AMOUNT'].map(str)
        dfToPrint1['AMOUNT'].ix[dfToPrint1['AMOUNT']=='-1.0'] = ''
    dfToPrint1 = dfToPrint1[['T_NAME','TEXT','AMOUNT','T_CRED','PAYM']]
    
    dfToPrint2['T_NAME'].ix[dfToPrint2['T_NAME'].isnull()] = ''
    dfToPrint2['TEXT'].ix[dfToPrint2['TEXT'].isnull()] = ''
    dfToPrint2['PAYM'].ix[dfToPrint2['PAYM'].isnull()] = ''
    dfToPrint2['T_CRED'].ix[dfToPrint2['T_CRED'].isnull()] = ''
    dfToPrint2['AMOUNT'].ix[dfToPrint2['AMOUNT'].isnull()] = -1
    dfToPrint2['AMOUNT']=dfToPrint2['AMOUNT'].map(str)
    dfToPrint2['AMOUNT'].ix[dfToPrint2['AMOUNT']=='-1.0'] = ''
    dfToPrint2 = dfToPrint2[['T_NAME','TEXT','AMOUNT','T_CRED','PAYM']]
    
    return {
        'dfSummary': dfToPrint1,
        'dfSynthesis': dfToPrint2,
        }

def _appendLineToVatLiquidationDict(liqDict, text, namSeq, dbt, crt):
    liqDict['TEXT'].append(text)
    liqDict['SEQUENCE'].append(namSeq)
    liqDict['DBT'].append(dbt)
    liqDict['CRT'].append(crt)

def addLiquidationSummaryFinalResults(vatDf, periodDf, debitVat, creditVat,
                                    companyName, onlyValidatedMoves, treasuryVatAccountCode, 
                                    periodName=None, fiscalyearName=None, liquidationDict=None):
    '''
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
        'SEQUENCE': [],
        'DBT': [],
        'CRT': [],
        }
    df0 = vatDf.copy()
    #aggiunta riga "IVA a debito o credito per il periodo"
    if debitVat >= creditVat:
        _appendLineToVatLiquidationDict(liquidationDict, "IVA a debito o credito per il periodo", "", debitVat-creditVat, 0)
    else:
        _appendLineToVatLiquidationDict(liquidationDict, "IVA a debito o credito per il periodo", "", 0, creditVat-debitVat)
    #aggiunta riga "Debito (non superiore a 25,82 Euro) o credito da periodo precedente + acconti IVA"
    if periodName:
        df1 = periodDf.ix[periodDf['NAM_PRD']==periodName].reset_index()
        dateStart = df1[0:1]['FY_DATE_START'][0]
        dateStop = df1[0:1]['P_DATE_STOP'][0]
        df0 = df0.ix[(df0['DATE']>=dateStart) & (df0['DATE']<=dateStop)]
    else:
        df0 = df0.ix[df0['ESER']==fiscalyearName]
    df0 = df0.ix[df0["T_ACC"]==treasuryVatAccountCode].reset_index(drop=True)
    df0 = df0[['CRED','AMOUNT']]
    df0 = df0.groupby('CRED').sum()[['AMOUNT']].reset_index()
    df1 = df0.ix[df0['CRED']==True].reset_index()
    df2 = df0.ix[df0['CRED']==False].reset_index()
    debitFromPreviousPeriod = 0
    creditFromPreviousPeriod = 0
    if len(df2['AMOUNT']) > 0:
        debitFromPreviousPeriod = df2['AMOUNT'][0]
    if len(df1['AMOUNT']) > 0:
        creditFromPreviousPeriod = df1['AMOUNT'][0]
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

def getVatLiquidationSummary(vatDf, periodDf, companyName, onlyValidatedMoves, treasuryVatAccountCode, periodName=None, fiscalyearName=None):
    '''
    funzione che restituisce il riepilogo di liquidazione iva
    Il periodo (o l'anno fiscale) deve essere passato come parametro
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
         'SEQUENCE': [],
         'DBT': [],
         'CRT': [],
         }
    
    #recupero il nome delle sequenze iva per cui ci sono dei movimenti nel periodo d'interesse
    df1 = vatDf[['SEQUENCE']]
    df1 = df1.drop_duplicates()
    vatSequences = list(df1['SEQUENCE'])
    #definizione variabili per totali iva a credito e a debito
    creditVatTotal = 0
    debitVatTotal = 0
    _appendLineToVatLiquidationDict(vatLiquidationDict,"IVA ad esigibilita' immediata","","","")
    #recupero informazioni riepiloghi iva (per iva immediata)
    for sequence in vatSequences:
        vatSummary = getVatSummary(vatDf, companyName, onlyValidatedMoves, periodName=periodName, sequenceName=sequence)
        immediateDebitTotal = 0
        immediateCreditTotal = 0
        immediateTotalsDf = vatSummary.ix[(vatSummary['TOTAL']==True) & (vatSummary['T_IMM']==True)].reset_index()
        if len(immediateTotalsDf['TAX_DEB']) > 0:
            immediateDebitTotal = immediateTotalsDf['TAX_DEB'][0]
        if len(immediateTotalsDf['TAX_CRED']) > 0:
            immediateCreditTotal = immediateTotalsDf['TAX_CRED'][0]
        if (immediateDebitTotal != 0) or (immediateCreditTotal != 0):
            _appendLineToVatLiquidationDict(vatLiquidationDict,"",sequence,immediateDebitTotal,immediateCreditTotal)
            creditVatTotal += immediateCreditTotal
            debitVatTotal += immediateDebitTotal
    #recupero informazioni per iva ad esig. differita
    deferredSummary = getDeferredVatSummary(vatDf, companyName, onlyValidatedMoves, periodDf,
                        paymentsPeriodName=periodName, paymentsFiscalyearName=fiscalyearName)
    dfSynthesis = deferredSummary['dfSynthesis']
    deferredDebitTotalDf = dfSynthesis.ix[(dfSynthesis['PAYM']==True) & (dfSynthesis['T_CRED']==False)].reset_index()
    deferredCreditTotalDf = dfSynthesis.ix[(dfSynthesis['PAYM']==True) & (dfSynthesis['T_CRED']==True)].reset_index()
    deferredDebitTotal = float (deferredDebitTotalDf['AMOUNT'][0])
    deferredCreditTotal = float (deferredCreditTotalDf['AMOUNT'][0])
    _appendLineToVatLiquidationDict(vatLiquidationDict,"IVA esigibile da esigibilita' differita","",deferredDebitTotal,deferredCreditTotal)
    creditVatTotal += deferredCreditTotal
    debitVatTotal += deferredDebitTotal
    _appendLineToVatLiquidationDict(vatLiquidationDict,"Totale","",debitVatTotal,creditVatTotal)
    #aggiunta righe finali
    vatLiquidationDict = addLiquidationSummaryFinalResults(
                                        vatDf, periodDf, debitVatTotal, creditVatTotal, 
                                        companyName, onlyValidatedMoves, treasuryVatAccountCode, periodName=periodName, 
                                        fiscalyearName=fiscalyearName, liquidationDict=vatLiquidationDict)
    vatLiquidationDf = pandas.DataFrame(vatLiquidationDict)
    vatLiquidationDf = vatLiquidationDf[['TEXT','SEQUENCE','DBT','CRT']]
    return vatLiquidationDf
    
def getVatControlSummary(fiscalyearName, vatSummary, vatDf, periodDf, companyName, 
                        onlyValidatedMoves, treasuryVatAccountCode):
    '''
    funzione che restituisce il df con il prospetto di controllo d'esercizio
    ESER        anno fiscale
    M_NUM       numero di protocollo
    M_NAME      name della move
    M_REF       riferimento della move
    CASH        booleano che indica se è un pagamento di iva differita, altrimenti è None
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
    immediateCreditVat = 0
    immediateDebitVat = 0
    df0 = vatSummary.ix[(vatSummary['TOTAL']==True) & (vatSummary['T_IMM']==True)].reset_index()
    if len(df0)>0:
        immediateCreditVat = df0['TAX_CRED'][0]
        immediateDebitVat = df0['TAX_DEB'][0]
    #recupero iva differita (a credito e a debito)
    deferredCreditVat = 0
    deferredDebitVat = 0
    df0 = vatSummary.ix[(vatSummary['TOTAL']==True) & (vatSummary['T_IMM']==False)].reset_index()
    if len(df0)>0:
        deferredCreditVat = df0['TAX_CRED'][0]
        deferredDebitVat = df0['TAX_DEB'][0]
    #calcolo iva differita divenuta esigibile dall'esercizio precedente
    previousDeferredVatCredit = 0
    previousDeferredVatDebit = 0
    dfPeriods1 = periodDf[['FY_DATE_START','NAM_FY']]
    dfPeriods1 = dfPeriods1.drop_duplicates()
    df0 = dfPeriods1.ix[dfPeriods1['NAM_FY']==fiscalyearName].reset_index()
    fiscalyearDateStart = df0[0:1]['FY_DATE_START'][0]
    previousFiscalyearDateStart = date(fiscalyearDateStart.year-1,fiscalyearDateStart.month,fiscalyearDateStart.day)
    df0 = dfPeriods1.ix[dfPeriods1['FY_DATE_START']==previousFiscalyearDateStart].reset_index()
    if len(df0) > 0:
        previousFiscalyearName = df0['NAM_FY'][0]
        deferredSummary = getDeferredVatSummary(vatDf, companyName, onlyValidatedMoves, periodDf,
                        billsFiscalyearName=previousFiscalyearName, paymentsFiscalyearName=fiscalyearName)
        deferredSummarySynthesis = deferredSummary['dfSynthesis']
        df0 = deferredSummarySynthesis.ix[(deferredSummarySynthesis['PAYM']==True) & 
                                            (deferredSummarySynthesis['T_CRED']==True)].reset_index()
        if len(df0) > 0:
            previousDeferredVatCredit = df0['AMOUNT'][0]
        df0 = deferredSummarySynthesis.ix[(deferredSummarySynthesis['PAYM']==True) & 
                                            (deferredSummarySynthesis['T_CRED']==False)].reset_index()
        if len(df0) > 0:
            previousDeferredVatDebit = df0['AMOUNT'][0]
    #calcolo iva differita divenuta esigibile dall'esercizio corrente
    currentDeferredVatCredit = 0
    currentDeferredVatDebit = 0
    deferredSummary = getDeferredVatSummary(vatDf, companyName, onlyValidatedMoves, periodDf,
                        billsFiscalyearName=fiscalyearName, paymentsFiscalyearName=fiscalyearName)
    deferredSummarySynthesis = deferredSummary['dfSynthesis']
    df0 = deferredSummarySynthesis.ix[(deferredSummarySynthesis['PAYM']==True) & 
                                        (deferredSummarySynthesis['T_CRED']==True)].reset_index()
    if len(df0) > 0:
        currentDeferredVatCredit = df0['AMOUNT'][0]
    df0 = deferredSummarySynthesis.ix[(deferredSummarySynthesis['PAYM']==True) & 
                                        (deferredSummarySynthesis['T_CRED']==False)].reset_index()
    if len(df0) > 0:
        currentDeferredVatDebit = df0['AMOUNT'][0]
    #calcolo totali
    currentDeferredVatCredit = float(currentDeferredVatCredit)
    currentDeferredVatDebit = float(currentDeferredVatDebit)
    previousDeferredVatCredit = float(previousDeferredVatCredit)
    previousDeferredVatDebit = float(previousDeferredVatDebit)
    immediateCreditVat = float(immediateCreditVat)
    immediateDebitVat = float(immediateDebitVat)
    deferredCreditVat = float(deferredCreditVat)
    deferredDebitVat = float(deferredDebitVat)
    creditDeferredVatNowExigible = currentDeferredVatCredit + previousDeferredVatCredit
    debitDeferredVatNowExigible = currentDeferredVatDebit + previousDeferredVatDebit
    creditTotalVatExigible = creditDeferredVatNowExigible + immediateCreditVat
    debitTotalVatExigible = debitDeferredVatNowExigible + immediateDebitVat
    creditDeferredVatExigibleInNextExercise = deferredCreditVat - currentDeferredVatCredit
    debitDeferredVatExigibleInNextExercise = deferredDebitVat - currentDeferredVatDebit
    #costruzione dataframe di Riepilogo con IVA diventata esigibile
    summaryDict = {
        'TEXT': ["IVA AD ESIG. IMMEDIATA REGISTRATA NELL'ESERCIZIO",
                "IVA AD ESIG. DIFFERITA REGISTRATA NELL'ESERCIZIO",
                "",
                "IVA AD ESIG. DIFFERITA ESIGIBILE NELL' ESERCIZIO - registrata nell'esercizio precedente",
                "IVA AD ESIG. DIFFERITA ESIGIBILE NELL' ESERCIZIO - registrata nell'esercizio corrente",
                "TOTALE IVA AD ESIG. DIFFERITA ESIGIBILE NELL' ESERCIZIO",
                "",
                "TOTALE IVA ESIGIBILE NELL'ESERCIZIO CORRENTE",
                "",
                "IVA AD ESIGIBILITA' DIFFERITA DA ESIGERE NELL'ESERCIZIO SUCCESSIVO",
                ],
        'DBT': [
            immediateDebitVat,
            deferredDebitVat,
            "",
            previousDeferredVatDebit,
            currentDeferredVatDebit,
            debitDeferredVatNowExigible,
            "",
            debitTotalVatExigible,
            "",
            debitDeferredVatExigibleInNextExercise,
            ],
        'CRT': [
            immediateCreditVat,
            deferredCreditVat,
            "",
            previousDeferredVatCredit,
            currentDeferredVatCredit,
            creditDeferredVatNowExigible,
            "",
            creditTotalVatExigible,
            "",
            creditDeferredVatExigibleInNextExercise,
            ],
        }
    summaryDf = pandas.DataFrame(summaryDict)
    summaryDf = summaryDf[['TEXT','DBT','CRT']]
    #aggiunta righe finali liquidazione iva
    vatLiquidationDict = addLiquidationSummaryFinalResults(
                                        vatDf, periodDf, immediateDebitVat + debitDeferredVatNowExigible,
                                        immediateCreditVat + creditDeferredVatNowExigible, companyName, 
                                        onlyValidatedMoves, treasuryVatAccountCode, fiscalyearName=fiscalyearName)
    vatLiquidationDf = pandas.DataFrame(vatLiquidationDict)
    vatLiquidationDf = vatLiquidationDf[['TEXT','DBT','CRT']]
    return {
        'summary' : summaryDf,
        'liquidationSummary': vatLiquidationDf,
        }

if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
