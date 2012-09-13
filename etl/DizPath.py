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

__VERSION__ = '0.1'
__AUTHOR__ = 'Luigi Cirillo (<luigi.cirillo@servabit.it>)'

import sys
import os
import pandas
import MySQLdb
try:
    import cPickle
except ImportError:
    import Pickle as cPickle

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

import DBmap2
import create_dict
from share import Stark
from share.config import Config

def CreateDWComp(companyName):
    '''Questa funzione serve a generare per una Comoany i diversi file pickle che compongono il
       Datawarehouse di quella impresa
    ''' 
    configFilePath = os.path.join(BASEPATH,"config","goal2stark.cfg")
    config = Config(configFilePath)
    config.parse()
    if not companyName:
        companyName=config.options.get('company',False)
    picklesPath = config.options.get('pickles_path',False)
    immediateVatCreditAccountCode=config.options.get('immediate_credit_vat_account_code',False)
    immediateVatDebitAccountCode=config.options.get('immediate_debit_vat_account_code',False)
    deferredVatCreditAccountCode=config.options.get('deferred_credit_vat_account_code',False)
    deferredVatDebitAccountCode=config.options.get('deferred_debit_vat_account_code',False)
    treasuryVatAccountCode=config.options.get('treasury_vat_account_code',False)
    path = os.path.join(picklesPath,companyName)
    
    ############################################################################################
    #  importazione dei dati della classe Account Account
    #  contenente le informazioni sui conti del piano dei conti
    ############################################################################################
    ACCD = {
             'ID0_CON' : ('id', None), 
             'NAM_CON' : ('name', None),
             'COD_CON' : ('code', None),
             'NAM_IMP' : ('company', ('name', None)), 
             'GOV_CON' : ('account_type', ('name', None)),
             'TYP_CON' : ('type', None),
             'PAN_CON' : ('parent', ('name', None)),
             'PAC_CON' : ('parent', ('code', None))
             }

    #assegno a ACC la classe AccountAccount
    ACC = DBmap2.AccountAccount
    #costruisco il dizionario con le variabili selezionata
    DIZ_ACC = create_dict.create_dict(ACC, ACCD, companyName)
    accountsDf = pandas.DataFrame(DIZ_ACC)
    #Seleziono i dati per l'impresa Servabit
    #accountsDf=accountsDf[accountsDf['NAM_IMP']==companyName]
    del accountsDf['NAM_IMP']
    del accountsDf['TYP_CON']
    ACC = Stark(accountsDf,TYPE='elab',COD='ACC')
    #effettuo il primo abbellimento di Stark
    ACC.DES['ID0_CON']['DESVAR']=unicode('ID identificativo del conto','utf-8')
    ACC.DES['NAM_CON']['DESVAR']=unicode('Nome descrittivo del conto','utf-8')
    ACC.DES['COD_CON']['DESVAR']=unicode('Codice menorico identificativo del conto','utf-8')
    ACC.DES['GOV_CON']['DESVAR']=unicode('Tipologia che governa la gestione del conto','utf-8')
    ACC.DES['PAN_CON']['DESVAR']=unicode('Nome descrittivo del conto padre','utf-8')
    ACC.DES['PAC_CON']['DESVAR']=unicode('Codice menorico del conto padre','utf-8')
#    ACC.DefPathPkl(path)
    ACC.save(os.path.join(path, 'ACC.pickle'))

    ############################################################################################
    #  importazione dei dati della classe Account Move Line
    #  contenente le informazioni sulle line di scrittura contabile
    ############################################################################################
    MVLD = {
             'ID0_MVL' : ('id', None), 
             'NAM_MOV' : ('move', ('name', None)),
             'REF_MOV' : ('move', ('ref', None)), 
             'CHK_MOV' : ('move', ('to_check', None)),
             'STA_MOV'  : ('move', ('state', None)),
             'DAT_DOC' : ('move', ('invoice', ('date_document', None))),
             'NAM_MVL' : ('name', None),
             'COD_CON' : ('account', ('code', None)),
             'NAM_IMP'  : ('company', ('name', None)),
             'REF_MVL'  : ('ref', None),
             'DAT_MVL'  : ('date', None),
             'NAM_PRD'  : ('period', ('name', None)),
             'NAM_FY'  : ('period', ('fiscalyear', ('name', None))),
             'NAM_PAR'  : ('partner', ('name', None)),
             'NAM_CON'  : ('account', ('name', None)),
             'NAM_JRN'  : ('journal', ('name', None)),
             'TYP_JRN' : ('journal', ('type', None)), 
             'DBT_MVL'  : ('debit', None),
             'CRT_MVL'  : ('credit', None),
             'NAM_REC'  : ('reconcile', ('name', None)),
             'NAM_REC_P'  : ('reconcile_partial', ('name', None)),
             'TAX_COD'  : ('tax_code_id', None), 
             'TAX_AMO'  : ('tax_amount', None), 
             'NAM_SEQ'  : ('journal', ('sequence', ('name', None))), 
             'COD_SEQ'  : ('journal', ('sequence', ('code', None))), 
             }
    #assegno a MOVL la classe AccountMoveLine
    MVL = DBmap2.AccountMoveLine
    #costruisco il dizionario con le variabili selezionata
    DIZ_MVL = create_dict.create_dict(MVL, MVLD, companyName)
    movelineDf = pandas.DataFrame(DIZ_MVL)
    #Seleziono i dati per l'impresa Servabit
    #movelineDf=movelineDf[movelineDf['NAM_IMP']==companyName]
    del movelineDf['NAM_IMP']
    #del movelineDf['TYP_CON']
    MVL = Stark(movelineDf,TYPE='elab',COD='MVL')
    #effettuo il primo abbellimento di Stark
    MVL.DES['ID0_MVL']['DESVAR']=unicode('ID identificativo della move line','utf-8')
    MVL.DES['NAM_MVL']['DESVAR']=unicode('Nome descrittivo della move line','utf-8')
    MVL.DES['COD_CON']['DESVAR']=unicode('Codice mnemonico identificativo del conto','utf-8')
    MVL.DES['DAT_MVL']['DESVAR']=unicode('data di registrazione','utf-8')
    MVL.DES['STA_MOV']['DESVAR']=unicode('stato della move in termini di validazione','utf-8')
    MVL.DES['DBT_MVL']['DESVAR']=unicode('colonna DARE della partita doppia','utf-8')
    MVL.DES['CRT_MVL']['DESVAR']=unicode('colonna AVERE della partita doppia','utf-8')
    MVL.DES['TAX_COD']['DESVAR']=unicode("identificativo relativo al tax_code",'utf-8')
    MVL.DES['TAX_AMO']['DESVAR']=unicode("ammontare di tassa o imponibile",'utf-8')
    MVL.DES['DAT_DOC']['DESVAR']=unicode("la data della fattura",'utf-8')
    MVL.save(os.path.join(path, 'MVL.pickle'))


############################################################################################
    #  importazione dei dati della classe Account Move 
    #  contenente le informazioni sulle line di scrittura contabile
    ############################################################################################
    #MOVD = {
             #'ID0_MOL' : ('id', None), 
             #'NAM_MOV' : ('name', None), 
             #'REF_MOV' : ('ref', None),
             #'DAT_MOV' : ('date', None),
             #'NAM_PRD'  : ('period', ('name', None)),
             #'NAM_JRN'  : ('journal', ('name', None)),
             #'TYPE_JRN'  : ('journal', ('type', None)), #aggiunto da Nicola il 23/7/2012
             #'NAM_IMP'  : ('company', ('name', None)),
             #'NAM_PAR'  : ('partner', ('name', None)),
             #'CHK_MOV'  : ('to_check', None),
             #'STA_MOV'  : ('state', None),
             #'DATE_DOC' : ('invoice', ('date_document', None)), #aggiunto da Nicola il 13/7/2012
             #}
    ##assegno a MOVL la classe AccountMoveLine
    #MOV = DBmap2.AccountMove
    ##costruisco il dizionario con le variabili selezionata
    #DIZ_MOV = create_dict.create_dict(MOV, MOVD, companyName)
    #moveDf=pandas.DataFrame(DIZ_MOV)
    ##Seleziono i dati per l'impresa Servabit
    ##moveDf=moveDf[moveDf['NAM_IMP']==companyName]
    #del moveDf['NAM_IMP']
    ##del moveDf['TYP_CON']
    #MOV = Stark(moveDf,TYPE='elab',COD='MOV')
    ##effettuo il primo abbellimento di Stark
    #MOV.DES['ID0_MOL']['DESVAR']=unicode('ID identificativo della move','utf-8')
    #MOV.DES['NAM_MOV']['DESVAR']=unicode('Nome descrittivo della move','utf-8')
    #MOV.DES['NAM_PAR']['DESVAR']=unicode('Partner associato alla move','utf-8')
    #MOV.DES['DATE_DOC']['DESVAR']=unicode("E' la data della fattura (se la move è associata ad una fattura)",'utf-8')
    #MOV.DefPathPkl(path)
    #MOV.Dumpk('MOV.pickle')

############################################################################################
    #  importazione dei dati della classe Partner 
    #  contenente le informazioni sulle line di scrittura contabile
    ############################################################################################
    PARD = {
             'ID0_PAR' : ('id', None), 
             'NAM_PAR' : ('name', None), 
             'CFS_PAR' : ('tax', None),
             'IVA_PAR' : ('vat', None),
             'NAM_IMP'  : ('company', ('name', None)),
             }
    #assegno a MOVL la classe AccountMoveLine
    PAR = DBmap2.ResPartner
    #costruisco il dizionario con le variabili selezionata
    DIZ_PAR = create_dict.create_dict(PAR, PARD, companyName)
    partnerDf=pandas.DataFrame(DIZ_PAR)
    #Seleziono i dati per l'impresa Servabit
    #partnerDf=partnerDf[partnerDf['NAM_IMP']==companyName]
    del partnerDf['NAM_IMP']
    #del partnerDf['TYP_CON']
    PAR = Stark(partnerDf,TYPE='elab',COD='PAR')
    #effettuo il primo abbellimento di Stark
    PAR.DES['ID0_PAR']['DESVAR']=unicode('ID identificativo del partner','utf-8')
    PAR.DES['NAM_PAR']['DESVAR']=unicode('Nome descrittivo del partner','utf-8')
    PAR.DES['CFS_PAR']['DESVAR']=unicode('Codice fiscale del partner','utf-8')
    PAR.DES['IVA_PAR']['DESVAR']=unicode('Partita IVA del partner','utf-8')
    # PAR.DefPathPkl(path)
    PAR.save(os.path.join(path, 'PAR.pickle'))
    
    
    ############################################################################################
    #  importazione dei dati della classe Account Tax
    #  contenente le informazioni sulle tasse
    ############################################################################################
    TAX_D = {
             'NAM_TAX' : ('name', None),
             'TAX_CODE' : ('tax_code_id', None),
             'BASE_CODE' : ('base_code_id', None),
             'REF_TAX_CODE' : ('ref_tax_code_id', None),
             'REF_BASE_CODE' : ('ref_base_code_id', None),
             'NAM_IMP'  : ('company', ('name', None)),
             }
    #assegno a MOVL la classe AccountMoveLine
    TAX = DBmap2.AccountTax
    #costruisco il dizionario con le variabili selezionata
    DIZ_TAX = create_dict.create_dict(TAX, TAX_D, companyName)
    taxDf=pandas.DataFrame(DIZ_TAX)
    #Seleziono i dati per l'impresa Servabit
    #taxDf=taxDf[taxDf['NAM_IMP']==companyName]
    del taxDf['NAM_IMP']
    #del taxDf['TYP_CON']
    TAX = Stark(taxDf,TYPE='elab',COD='TAX')
    #effettuo il primo abbellimento di Stark
    TAX.DES['NAM_TAX']['DESVAR']=unicode("nome della tassa",'utf-8')
    TAX.DES['TAX_CODE']['DESVAR']=unicode("identificativo del tax_code di tassa",'utf-8')
    TAX.DES['BASE_CODE']['DESVAR']=unicode("identificativo del tax_code di imponibile",'utf-8')
    TAX.DES['REF_TAX_CODE']['DESVAR']=unicode("identificativo del tax_code di tassa (per le note di credito)",'utf-8')
    TAX.DES['REF_BASE_CODE']['DESVAR']=unicode("identificativo del tax_code di imponibile (per le note di credito)",'utf-8')
    TAX.save(os.path.join(path, 'TAX.pickle'))
    
    ############################################################################################
    #  importazione dei dati della classe AccountPeriod
    #  contenente le informazioni sui periodi
    ############################################################################################
    PERIOD_D = {
                'NAM_PRD' : ('name', None),
                'P_DATE_STR' : ('date_start', None),
                'P_DATE_STOP' : ('date_stop', None),
                'FY_DATE_START' : ('fiscalyear', ('date_start', None)),
                'FY_DATE_STOP' : ('fiscalyear', ('date_stop', None)),
                'NAM_FY' : ('fiscalyear', ('name', None)),
                'NAM_IMP'  : ('company', ('name', None)),
                }
    #assegno a MOVL la classe AccountMoveLine
    PERIOD = DBmap2.AccountPeriod
    #costruisco il dizionario con le variabili selezionata
    DIZ_PRD = create_dict.create_dict(PERIOD, PERIOD_D, companyName)
    periodDf = pandas.DataFrame(DIZ_PRD)
    #Seleziono i dati per l'impresa Servabit
    #periodDf=periodDf[periodDf['NAM_IMP']==companyName]
    del periodDf['NAM_IMP']
    #del periodDf['TYP_CON']
    PERIOD = Stark(periodDf,TYPE='elab',COD='PERIOD')
    #effettuo il primo abbellimento di Stark
    PERIOD.DES['P_DATE_STR']['DESVAR']=unicode("data di inizio del periodo",'utf-8')
    PERIOD.DES['P_DATE_STOP']['DESVAR']=unicode("data di fine del periodo",'utf-8')
    PERIOD.DES['FY_DATE_START']['DESVAR']=unicode("data di inizio dell'anno fiscale",'utf-8')
    PERIOD.DES['FY_DATE_STOP']['DESVAR']=unicode("data di fine dell'anno fiscale",'utf-8')
    PERIOD.DES['NAM_FY']['DESVAR']=unicode("nome dell'anno fiscale relativo al periodo",'utf-8')
#    PERIOD.DefPathPkl(path)
    PERIOD.save(os.path.join(path, 'PERIOD.pickle'))

    ############################################################################################
    #  importazione dei dati della classe IrSequence
    #  contenente le informazioni sui periodi
    ############################################################################################
    #SEQ_D = {
            #'NAM_SEQ' : ('name', None),
            #'COD_SEQ' : ('code', None),
            #'NAM_IMP'  : ('company', ('name', None)),
            #}
    ##assegno a MOVL la classe AccountMoveLine
    #SEQUENCE = DBmap2.IrSequence
    ##costruisco il dizionario con le variabili selezionata
    #DIZ_SEQ = create_dict.create_dict(SEQUENCE, SEQ_D, companyName)
    #sequenceDf=pandas.DataFrame(DIZ_SEQ)
    ##Seleziono i dati per l'impresa Servabit
    ##sequenceDf=sequenceDf[sequenceDf['NAM_IMP']==companyName]
    #del sequenceDf['NAM_IMP']
    ##del sequenceDf['TYP_CON']
    #SEQUENCE = Stark(sequenceDf,TYPE='elab',COD='SEQUENCE')
    ##effettuo il primo abbellimento di Stark
    #SEQUENCE.DES['COD_SEQ']['DESVAR']=unicode("codice della sequenza",'utf-8')
    #SEQUENCE.DES['NAM_SEQ']['DESVAR']=unicode("nome della sequenza",'utf-8')
    #SEQUENCE.save(os.path.join(path, 'SEQUENCE.pickle'))
    
    ############################################################################################
    #  creazione del dataframe specifico per i report iva
    ############################################################################################
    moveLineDf = movelineDf.rename(columns={'NAM_MOV' : 'M_NAME',
                                            'REF_MOV' : 'M_REF',
                                            'STA_MOV' : 'STATE',
                                            'DAT_DOC' : 'DATE_DOC',
                                            'COD_CON' : 'T_ACC',
                                            'DAT_MVL' : 'DATE',
                                            'NAM_PRD' : 'PERIOD',
                                            'NAM_FY' : 'ESER',
                                            'NAM_PAR' : 'PARTNER',
                                            'NAM_JRN' : 'JOURNAL',
                                            'NAM_REC' : 'RECON',
                                            'NAM_REC_P' : 'RECON_P',
                                            'NAM_SEQ' : 'SEQUENCE',
                                            'COD_CON' : 'T_ACC',
                                            })
    
    vatDatasDf = moveLineDf.ix[(moveLineDf["COD_SEQ"]=='RIVA') & (moveLineDf["TAX_COD"].notnull())].reset_index()
    #aggiunta colonne T_NAME e T_TAX
    df3 = pandas.DataFrame()
    df4 = pandas.DataFrame()
    df6 = pandas.DataFrame()
    df7 = pandas.DataFrame()
    df2 = vatDatasDf[vatDatasDf['TYP_JRN'].isin(['sale', 'purchase'])]
    try:
        df3 = pandas.merge(df2,taxDf,left_on='TAX_COD',right_on='TAX_CODE')
        df3['T_TAX'] = True
    except IndexError:
        pass
    try:
        df4 = pandas.merge(df2,taxDf,left_on='TAX_COD',right_on='BASE_CODE')
        df4['T_TAX'] = False
    except IndexError:
        pass
    df5 = vatDatasDf[vatDatasDf['TYP_JRN'].isin(['sale_refund', 'purchase_refund'])]
    try:
        df6 = pandas.merge(df5,taxDf,left_on='TAX_COD',right_on='REF_TAX_CODE')
        df6['T_TAX'] = True
    except IndexError:
        pass
    try:
        df7 = pandas.merge(df5,taxDf,left_on='TAX_COD',right_on='REF_BASE_CODE')
        df7['T_TAX'] = False
    except IndexError:
        pass
    vatDatasDf = pandas.concat([df3,df4,df6,df7]).reset_index(drop=True)
    #del vatDatasDf["TAX_CODE"]
    #del vatDatasDf["BASE_CODE"]
    #del vatDatasDf["REF_TAX_CODE"]
    #del vatDatasDf["REF_BASE_CODE"]
    #aggiunta a vatDatasDf delle move.line relative ai pagamenti dell'iva differita
    df0 = vatDatasDf.ix[(vatDatasDf["T_ACC"]==deferredVatCreditAccountCode) | (vatDatasDf["T_ACC"]==deferredVatDebitAccountCode)].reset_index()
    reconcileDf = df0[["RECON","RECON_P"]].drop_duplicates().reset_index(drop=True)
    reconcileDf['RECON'].ix[reconcileDf['RECON'].isnull()] = "NULL"
    reconcileDf['RECON_P'].ix[reconcileDf['RECON_P'].isnull()] = "NULL"
    df0 = moveLineDf.ix[moveLineDf["COD_SEQ"]!='RIVA'].reset_index()
    df1 = pandas.DataFrame()
    df2 = pandas.DataFrame()
    try:
        df1 = pandas.merge(df0,reconcileDf,on="RECON").reset_index(drop=True)
    except IndexError:
        pass
    try:
        df2 = pandas.merge(df0,reconcileDf,on="RECON_P").reset_index(drop=True)
    except IndexError:
        pass
    df3 = pandas.concat([df1,df2]).reset_index(drop=True)
    #del df3["RECON_P.x"]
    #del df3["RECON_P.y"]
    #del df3["RECON.x"]
    #del df3["RECON.y"]
    df3['T_TAX'] = True
    vatDatasDf = pandas.concat([vatDatasDf,df3]).reset_index(drop=True)
    #aggiunta a vatDatasDf delle move.line relative ai pagamenti dell'iva sul conto treasuryVatAccountCode
    df0 = moveLineDf.ix[moveLineDf["T_ACC"]==treasuryVatAccountCode].reset_index()
    vatDatasDf = pandas.concat([vatDatasDf,df0]).reset_index(drop=True)
    #del vatDatasDf["index"]
    vatDatasDf = vatDatasDf.rename(columns={'NAM_TAX' : 'T_NAME',
                                            })
    #costruzione delle altre colonne del df finale
    vatDatasDf['M_NUM'] = ''
    for i in range(len(vatDatasDf)):
        row = vatDatasDf[i:i+1]
        moveName = row['M_NAME'][i]
        moveNameSplits = moveName.split("/")
        vatDatasDf['M_NUM'][i:i+1] = moveNameSplits[len(moveNameSplits)-1]
    vatDatasDf['CASH'] = None
    for i in range(len(vatDatasDf)):
        row = vatDatasDf[i:i+1]
        debit = row['DBT_MVL'][i]
        credit = row['CRT_MVL'][i]
        accountCode = row['T_ACC'][i]
        if accountCode in [deferredVatDebitAccountCode,deferredVatCreditAccountCode]:
            vatDatasDf['CASH'][i:i+1] = (debit>0 and accountCode==deferredVatDebitAccountCode)\
                                        or (credit>0 and accountCode==deferredVatCreditAccountCode)
    
    vatDatasDf['CRED'] = True
    vatDatasDf['CRED'].ix[vatDatasDf['DBT_MVL']>0] = False
    
    vatDatasDf['AMOUNT'] = 0.00
    for i in range(len(vatDatasDf)):
        row = vatDatasDf[i:i+1]
        debit = row['DBT_MVL'][i]
        credit = row['CRT_MVL'][i]
        taxAmount = row['TAX_AMO'][i]
        journalType = row['TYP_JRN'][i]
        amount = None
        if taxAmount and taxAmount != 0:
            amount = taxAmount
        else:
            amount = max(debit,credit)
        if journalType in ['sale_refund','purchase_refund'] and (taxAmount==0 or not taxAmount):
            vatDatasDf['AMOUNT'][i:i+1] = -amount
        else:
            vatDatasDf['AMOUNT'][i:i+1] = amount
    
    vatDatasDf['T_CRED'] = None
    vatDatasDf['T_CRED'].ix[vatDatasDf['T_TAX']==True] = False
    vatDatasDf['T_CRED'].ix[(vatDatasDf['T_TAX']==True) & 
                             (vatDatasDf['T_ACC'].isin([immediateVatCreditAccountCode,deferredVatCreditAccountCode]))
                             ]= True
    vatDatasDf['T_CRED'].ix[(vatDatasDf['T_TAX']==True) & ((vatDatasDf['DBT_MVL']>0) | (vatDatasDf['TAX_AMO']<0)) &
                             (vatDatasDf['T_ACC']!=immediateVatDebitAccountCode) &
                             (vatDatasDf['T_ACC']!=deferredVatDebitAccountCode)
                             ]= True                       
    
    vatDatasDf['T_DET'] = None
    vatDatasDf['T_DET'].ix[vatDatasDf['T_TAX']==True] = False
    vatDatasDf['T_DET'].ix[(vatDatasDf['T_TAX']==True) & 
                            vatDatasDf['T_ACC'].isin([
                                    immediateVatCreditAccountCode,immediateVatDebitAccountCode,
                                    deferredVatCreditAccountCode,deferredVatDebitAccountCode])] = True
    vatDatasDf['T_IMM'] = None
    vatDatasDf['T_IMM'].ix[(vatDatasDf['T_TAX']==True) & (vatDatasDf['T_DET']==True)] = False
    vatDatasDf['T_IMM'].ix[(vatDatasDf['T_TAX']==True) & (vatDatasDf['T_DET']==True) & 
                            (vatDatasDf['T_ACC'].isin([immediateVatCreditAccountCode,immediateVatDebitAccountCode]))
                            ] = True
    vatDatasDf['T_EXI'] = None
    vatDatasDf['T_EXI'].ix[vatDatasDf['T_IMM']==False] = False
    vatDatasDf['T_EXI'].ix[vatDatasDf['T_IMM']==True] = True
    vatDatasDf['T_EXI'].ix[(vatDatasDf['T_IMM']==False) & (vatDatasDf['CASH']==True)] = True
    vatDatasDf = vatDatasDf[['DATE','DATE_DOC','PERIOD','ESER',
                            'M_NAME','M_REF','M_NUM','PARTNER','JOURNAL','SEQUENCE',
                            'STATE','T_NAME','RECON','RECON_P','CASH', 'CRED',
                            'T_ACC','T_TAX','T_CRED','T_DET','T_IMM','T_EXI','AMOUNT'
                            ]]
    vatDatasDf = vatDatasDf.sort(columns=['M_NAME'])
    vatDatasStark = Stark(vatDatasDf,TYPE='elab',COD='VAT')
    vatDatasStark.DES['ESER']['DESVAR']=unicode("anno fiscale",'utf-8')
    vatDatasStark.DES['M_NUM']['DESVAR']=unicode("numero di protocollo",'utf-8')
    vatDatasStark.DES['M_NAME']['DESVAR']=unicode("name della move",'utf-8')
    vatDatasStark.DES['M_REF']['DESVAR']=unicode("riferimento della move",'utf-8')
    vatDatasStark.DES['CASH']['DESVAR']=unicode("booleano che indica se è un pagamento",'utf-8')
    vatDatasStark.DES['T_NAME']['DESVAR']=unicode("nome dell'imposta",'utf-8')
    vatDatasStark.DES['T_ACC']['DESVAR']=unicode("codice del conto",'utf-8')
    vatDatasStark.DES['T_TAX']['DESVAR']=unicode("booleano che indica se è un'imposta (oppure un imponibile)",'utf-8')
    vatDatasStark.DES['T_CRED']['DESVAR']=unicode("booleano che indica se l'imposta è a credito",'utf-8')
    vatDatasStark.DES['T_DET']['DESVAR']=unicode("booleano che indica se l'imposta è detraibile",'utf-8')
    vatDatasStark.DES['T_IMM']['DESVAR']=unicode("booleano che indica se l'imposta è ad esigibilità immediata",'utf-8')
    vatDatasStark.DES['T_EXI']['DESVAR']=unicode("booleano che indica se l'imposta è esigibile nel periodo",'utf-8')
    vatDatasStark.DES['STATE']['DESVAR']=unicode("stato della scrittura contabile",'utf-8')
    vatDatasStark.DES['PERIOD']['DESVAR']=unicode("nome del periodo",'utf-8')
    vatDatasStark.DES['JOURNAL']['DESVAR']=unicode("nome del journal",'utf-8')
    vatDatasStark.DES['DATE_DOC']['DESVAR']=unicode("data della fattura",'utf-8')
    vatDatasStark.DES['DATE']['DESVAR']=unicode("data di registrazione",'utf-8')
    vatDatasStark.DES['PARTNER']['DESVAR']=unicode("nome del partner",'utf-8')
    vatDatasStark.DES['RECON']['DESVAR']=unicode("nome della riconciliazione",'utf-8')
    vatDatasStark.DES['RECON_P']['DESVAR']=unicode("nome della riconciliazione parziale",'utf-8')
    vatDatasStark.DES['AMOUNT']['DESVAR']=unicode("importo (di imponibile o imposta o pagamento)",'utf-8')
    vatDatasStark.DES['CRED']['DESVAR']=unicode("booleano che indica se l'importo originario era in dare o in avere",'utf-8')
    vatDatasStark.DES['SEQUENCE']['DESVAR']=unicode("nome della sequenza",'utf-8')
    vatDatasStark.save(os.path.join(path, 'VAT.pickle'))
    #vatDatasDf.to_csv("df"+companyName+".csv",sep=";",encoding="utf-8")
    
    ############################################################################################
    #  importazione dei dati della classe ResCompany
    #  contenente le informazioni sull'impresa
    ############################################################################################
    companyDict = {
             'NAME' : ('name', None),
             'TAX' : ('partner', ('tax', None)),
             'VAT' : ('partner', ('vat', None)),
             'ADDRESS' : ('partner', ('addresses', ('street', None))),
             'CITY' : ('partner', ('addresses', ('city', None))),
             'ZIP' : ('partner', ('addresses', ('zip', None))),
             'PHONE' : ('partner', ('addresses', ('phone', None))),
             }
    #assegno a MOVL la classe AccountMoveLine
    ResCompany = DBmap2.ResCompany
    #costruisco il dizionario con le variabili selezionata
    companyDict = create_dict.create_dict(ResCompany, companyDict, companyName)
    companyDf = pandas.DataFrame(companyDict)
    #Seleziono i dati per l'impresa Servabit
    companyDf = companyDf[companyDf['NAME']==companyName]
    companyDf = companyDf.reset_index(drop=True)
    ResCompanyStark = Stark(companyDf,TYPE='elab',COD='COM')
    #effettuo il primo abbellimento di Stark
    ResCompanyStark.DES['NAME']['DESVAR']=unicode("nome dell'azienda",'utf-8')
    ResCompanyStark.DES['TAX']['DESVAR']=unicode("codice fiscale",'utf-8')
    ResCompanyStark.DES['VAT']['DESVAR']=unicode("partita iva",'utf-8')
    ResCompanyStark.DES['ADDRESS']['DESVAR']=unicode("indirizzo",'utf-8')
    ResCompanyStark.DES['CITY']['DESVAR']=unicode("città",'utf-8')
    ResCompanyStark.DES['ZIP']['DESVAR']=unicode("cap",'utf-8')
    ResCompanyStark.DES['PHONE']['DESVAR']=unicode("telefono",'utf-8')
    ResCompanyStark.save(os.path.join(path, 'COMP.pickle'))
    
    ############################################################################################
    #  importazione dei dati della classe AccountInvoice
    #  contenente le informazioni sulle fatture
    ############################################################################################
    invoiceDict = {
             'NAME' : ('name', None),
             'DATE_INV' : ('date_invoice', None),
             'DATE_DUE' : ('date_due', None),
             'PERIOD' : ('period', ('name', None)),
             'ESER' : ('period', ('fiscalyear', ('name', None))),
             'JOURNAL' : ('journal', ('name', None)),
             'TYPE' : ('type', None),
             'STATE' : ('state', None),
             'NUM' : ('number', None),
             'PARTNER' : ('partner', ('name', None)),
             'TOTAL' : ('amount_total', None),
             'NAM_MOV': ('move', ('name', None)),
             }

    #assegno a ACC la classe AccountAccount
    invoiceClass = DBmap2.AccountInvoice
    #costruisco il dizionario con le variabili selezionata
    invoiceDict = create_dict.create_dict(invoiceClass, invoiceDict, companyName)
    invoiceDf = pandas.DataFrame(invoiceDict)
    #invoiceDf=invoiceDf[invoiceDf['NAM_IMP']==companyName]
    invoiceStark = Stark(invoiceDf,TYPE='elab',COD='INV')
    #effettuo il primo abbellimento di Stark
    invoiceStark.DES['NUM']['DESVAR']=unicode('numero fattura','utf-8')
    invoiceStark.DES['ESER']['DESVAR']=unicode("nome dell'anno fiscale",'utf-8')
    invoiceStark.DES['NAM_MOV']['DESVAR']=unicode("nome della scrittura contabile associata",'utf-8')
    invoiceStark.save(os.path.join(path, 'INV.pickle'))
    
    ############################################################################################
    #  importazione dei dati della classe AccountVoucher
    #  contenente le informazioni sulle fatture
    ############################################################################################
    voucherDict = {
             'NAME' : ('name', None),
             'DATE' : ('date', None),
             'DATE_DUE' : ('date_due', None),
             'PERIOD' : ('period', ('name', None)),
             'ESER' : ('period', ('fiscalyear', ('name', None))),
             'JOURNAL' : ('journal', ('name', None)),
             'TYPE' : ('type', None),
             'STATE' : ('state', None),
             'NUM' : ('number', None),
             'PARTNER' : ('partner', ('name', None)),
             'AMOUNT' : ('amount', None),
             'NAM_MOV': ('move', ('name', None)),
             }

    #assegno a ACC la classe AccountAccount
    voucherClass = DBmap2.AccountVoucher
    #costruisco il dizionario con le variabili selezionata
    voucherDict = create_dict.create_dict(voucherClass, voucherDict, companyName)
    voucherDf = pandas.DataFrame(voucherDict)
    #voucherDf=voucherDf[voucherDf['NAM_IMP']==companyName]
    voucherStark = Stark(voucherDf,TYPE='elab',COD='VOU')
    #effettuo il primo abbellimento di Stark
    voucherStark.DES['NUM']['DESVAR']=unicode('numero voucher','utf-8')
    voucherStark.DES['ESER']['DESVAR']=unicode("nome dell'anno fiscale",'utf-8')
    voucherStark.DES['NAM_MOV']['DESVAR']=unicode("nome della scrittura contabile associata",'utf-8')
    voucherStark.save(os.path.join(path, 'VOU.pickle'))