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

import sys
import os
import pandas
import sqlalchemy

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
import DBmap2
import create_dict
import parallel_jobs
from share import Stark
from share.config import Config


def create_dict(cl_dmap2, dict_path, company_name):
    '''
    crea un dizionario a partire dai dati contenuti nel db
    @param cl_dmap2: classe contenuta in DBmap2
    @param dict_path: dizionario strutturato come :
                    { 'NAMEVAR' :
                        ('name attribute cl_dmap2', (...., None))
    return dictionary {
                        'NAMEVAR' : [data, data, data, .....]
                        }
    '''
    
    def tuple2attr(obj, tpl):
        el = tpl
        while(el[1] != None):
            obj = getattr(obj, el[0])
            el = el[1]
        if isinstance(obj,sqlalchemy.orm.collections.InstrumentedList):
            obj = obj[0]
        obj = getattr(obj, el[0])
        return obj
    
    def get_obj(session, cl_dbmap2, company_name):
        objs = None
        try:
            getattr(cl_dbmap2, 'company')
            objs = session.query(cl_dbmap2).filter(cl_dbmap2.company.has(name=company_name)).all()
        except AttributeError:    
            objs = session.query(cl_dbmap2).all()
        return objs
    
    session = DBmap2.open_session()
    out_dict = {}    
    objs = get_obj(session, cl_dmap2, company_name)
    for key in dict_path.iterkeys():
        out_dict[key] = []
    for obj in objs:
        for key in dict_path.iterkeys():
            try:
                out_dict[key].append(tuple2attr(obj, dict_path[key]))
            except AttributeError:
                out_dict[key].append(None)
    DBmap2.close_session(session)
    return out_dict


def createDWComp(companyName,picklesPath,immediateVatCreditAccountCode,
                immediateVatDebitAccountCode,deferredVatCreditAccountCode,
                deferredVatDebitAccountCode,treasuryVatAccountCode):
    '''Questa funzione serve a generare per una Company i diversi file pickle che compongono il
       Datawarehouse di quella impresa
    ''' 
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
    DIZ_ACC = create_dict(ACC, ACCD, companyName)
    accountsDf = pandas.DataFrame(DIZ_ACC)
    #Seleziono i dati per l'impresa Servabit
    #accountsDf=accountsDf[accountsDf['NAM_IMP']==companyName]
    del accountsDf['NAM_IMP']
    ACC = Stark(accountsDf, os.path.join(path, 'ACC.pickle'))
    #effettuo il primo abbellimento di Stark
    ACC.VD = {
        'ID0_CON': {'DES': unicode('ID identificativo del conto','utf-8')},
        'NAM_CON': {'DES': unicode('Nome descrittivo del conto','utf-8')}, 
        'COD_CON': {'DES': unicode('Codice menorico identificativo del conto','utf-8')},
        'GOV_CON': {'DES': unicode('Tipologia che governa la gestione del conto','utf-8')},
        'PAN_CON': {'DES': unicode('Nome descrittivo del conto padre','utf-8')},
        'PAC_CON': {'DES': unicode('Codice menorico del conto padre','utf-8')},
        'TYP_CON': {'DES': unicode('Tipo interno','utf-8')},
        }
#    ACC.DefPathPkl(path)
    ACC.save()

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
             'TYP_CON' : ('account', ('type', None)),
             'NAM_IMP'  : ('company', ('name', None)),
             'REF_MVL'  : ('ref', None),
             'DAT_MVL'  : ('date', None),
             'DAT_DUE'  : ('date_maturity', None),
             'NAM_PRD'  : ('period', ('name', None)),
             'NAM_FY'  : ('period', ('fiscalyear', ('name', None))),
             'NAM_PAR'  : ('partner', ('name', None)),
             'NAM_CON'  : ('account', ('name', None)),
             'NAM_JRN'  : ('journal', ('name', None)),
             'TYP_JRN' : ('journal', ('type', None)), 
             'DBT_MVL'  : ('debit', None),
             'CRT_MVL'  : ('credit', None),
             'ID_REC'  : ('reconcile_id',  None),
             'ID_REC_P'  : ('reconcile_partial_id', None),
             'TAX_COD'  : ('tax_code_id', None), 
             'TAX_AMO'  : ('tax_amount', None), 
             'NAM_SEQ'  : ('journal', ('sequence', ('name', None))), 
             'COD_SEQ'  : ('journal', ('sequence', ('code', None))), 
             }
    #assegno a MOVL la classe AccountMoveLine
    MVL = DBmap2.AccountMoveLine
    #costruisco il dizionario con le variabili selezionata
    DIZ_MVL = create_dict(MVL, MVLD, companyName)
    movelineDf = pandas.DataFrame(DIZ_MVL)
    #Seleziono i dati per l'impresa Servabit
    #movelineDf=movelineDf[movelineDf['NAM_IMP']==companyName]
    del movelineDf['NAM_IMP']
    #del movelineDf['TYP_CON']
    MVL = Stark(movelineDf, os.path.join(path, 'MVL.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    MVL.VD = {
        'ID0_MVL': {'DES': unicode('ID identificativo della move line','utf-8')},
        'NAM_MVL': {'DES': unicode('Nome descrittivo della move line','utf-8')},
        'COD_CON': {'DES': unicode('Codice mnemonico identificativo del conto','utf-8')},
        'DAT_MVL': {'DES': unicode('data di registrazione','utf-8')},
        'STA_MOV': {'DES': unicode('stato della move in termini di validazione','utf-8')},
        'DBT_MVL': {'DES': unicode('colonna DARE della partita doppia','utf-8')},
        'CRT_MVL': {'DES': unicode('colonna AVERE della partita doppia','utf-8')},
        'TAX_COD': {'DES': unicode("identificativo relativo al tax_code",'utf-8')},
        'TAX_AMO': {'DES': unicode("ammontare di tassa o imponibile",'utf-8')},
        'TYP_CON': {'DES': unicode("è il tipo interno del conto associato alla move line",'utf-8')},
        'DAT_DOC': {'DES': unicode("la data della fattura",'utf-8')},
        'ID_REC': {'DES': unicode("id della riconciliazione",'utf-8')},
        'ID_REC_P': {'DES': unicode("id della riconciliazione parziale",'utf-8')},
        }
    MVL.save()

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
             #'TYPE_JRN'  : ('journal', ('type', None)),
             #'NAM_IMP'  : ('company', ('name', None)),
             #'NAM_PAR'  : ('partner', ('name', None)),
             #'CHK_MOV'  : ('to_check', None),
             #'STA_MOV'  : ('state', None),
             #'DATE_DOC' : ('invoice', ('date_document', None)),
             #}
    ##assegno a MOVL la classe AccountMoveLine
    #MOV = DBmap2.AccountMove
    ##costruisco il dizionario con le variabili selezionata
    #DIZ_MOV = create_dict(MOV, MOVD, companyName)
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
    DIZ_PAR = create_dict(PAR, PARD, companyName)
    partnerDf=pandas.DataFrame(DIZ_PAR)
    #Seleziono i dati per l'impresa Servabit
    #partnerDf=partnerDf[partnerDf['NAM_IMP']==companyName]
    del partnerDf['NAM_IMP']
    #del partnerDf['TYP_CON']
    PAR = Stark(partnerDf, os.path.join(path, 'PAR.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    PAR.VD = {
        'ID0_PAR': {'DES': unicode('ID identificativo del partner','utf-8')},
        'NAM_PAR': {'DES': unicode('Nome descrittivo del partner','utf-8')},
        'CFS_PAR': {'DES': unicode('Codice fiscale del partner','utf-8')},
        'IVA_PAR': {'DES': unicode('Partita IVA del partner','utf-8')},
        }
    # PAR.DefPathPkl(path)
    PAR.save()
    
    
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
    DIZ_TAX = create_dict(TAX, TAX_D, companyName)
    taxDf=pandas.DataFrame(DIZ_TAX)
    #Seleziono i dati per l'impresa Servabit
    #taxDf=taxDf[taxDf['NAM_IMP']==companyName]
    del taxDf['NAM_IMP']
    #del taxDf['TYP_CON']
    TAX = Stark(taxDf, os.path.join(path, 'TAX.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    TAX.VD = {
        'NAM_TAX': {'DES': unicode("nome della tassa",'utf-8')},
        'TAX_CODE': {'DES': unicode("identificativo del tax_code di tassa",'utf-8')},
        'BASE_CODE': {'DES': unicode("identificativo del tax_code di imponibile",'utf-8')},
        'REF_TAX_CODE': {'DES': unicode("identificativo del tax_code di tassa (per le note di credito)",'utf-8')},
        'REF_BASE_CODE': {'DES': unicode("identificativo del tax_code di imponibile (per le note di credito)",'utf-8')},
        }
    TAX.save()
    
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
    DIZ_PRD = create_dict(PERIOD, PERIOD_D, companyName)
    periodDf = pandas.DataFrame(DIZ_PRD)
    #Seleziono i dati per l'impresa Servabit
    #periodDf=periodDf[periodDf['NAM_IMP']==companyName]
    del periodDf['NAM_IMP']
    #del periodDf['TYP_CON']
    PERIOD = Stark(periodDf, os.path.join(path, 'PERIOD.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    PERIOD.VD = {
        'P_DATE_STR': {'DES': unicode("data di inizio del periodo",'utf-8')},
        'P_DATE_STOP': {'DES': unicode("data di fine del periodo",'utf-8')},
        'FY_DATE_START': {'DES': unicode("data di inizio dell'anno fiscale",'utf-8')},
        'FY_DATE_STOP': {'DES': unicode("data di fine dell'anno fiscale",'utf-8')},
        'NAM_FY': {'DES': unicode("nome dell'anno fiscale relativo al periodo",'utf-8')},
        }
    PERIOD.save()

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
    #DIZ_SEQ = create_dict(SEQUENCE, SEQ_D, companyName)
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
                                            'ID_REC' : 'RECON',
                                            'ID_REC_P' : 'RECON_P',
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
    if len(reconcileDf) > 0:
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
    vatDatasDf['T_DET'].ix[vatDatasDf['T_TAX'] == True] = False
    vatDatasDf['T_DET'].ix[(vatDatasDf['T_TAX'] == True) & 
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
    vatDatasStark = Stark(vatDatasDf, os.path.join(path, 'VAT.pickle'), TI='elab')
    vatDatasStark.VD = {
        'ESER': {'DES': unicode("anno fiscale",'utf-8')},
        'M_NUM': {'DES': unicode("numero di protocollo",'utf-8')},
        'M_NAME': {'DES': unicode("name della move",'utf-8')},
        'M_REF': {'DES': unicode("riferimento della move",'utf-8')},
        'CASH': {'DES': unicode("booleano che indica se è un pagamento",'utf-8')},
        'T_NAME': {'DES': unicode("nome dell'imposta",'utf-8')},
        'T_ACC': {'DES': unicode("codice del conto",'utf-8')},
        'T_TAX': {'DES': unicode("booleano che indica se è un'imposta (oppure un imponibile)",'utf-8')},
        'T_CRED': {'DES': unicode("booleano che indica se l'imposta è a credito",'utf-8')},
        'T_DET': {'DES': unicode("booleano che indica se l'imposta è detraibile",'utf-8')},
        'T_IMM': {'DES': unicode("booleano che indica se l'imposta è ad esigibilità immediata",'utf-8')},
        'T_EXI': {'DES': unicode("booleano che indica se l'imposta è esigibile nel periodo",'utf-8')},
        'STATE': {'DES': unicode("stato della scrittura contabile",'utf-8')},
        'PERIOD': {'DES': unicode("nome del periodo",'utf-8')},
        'JOURNAL': {'DES': unicode("nome del journal",'utf-8')},
        'DATE_DOC': {'DES': unicode("data della fattura",'utf-8')},
        'DATE': {'DES': unicode("data di registrazione",'utf-8')},
        'PARTNER': {'DES': unicode("nome del partner",'utf-8')},
        'RECON': {'DES': unicode("nome della riconciliazione",'utf-8')},
        'RECON_P': {'DES': unicode("nome della riconciliazione parziale",'utf-8')},
        'AMOUNT': {'DES': unicode("importo (di imponibile o imposta o pagamento)",'utf-8')},
        'CRED': {'DES': unicode("booleano che indica se l'importo originario era in dare o in avere",'utf-8')},
        'SEQUENCE': {'DES': unicode("nome della sequenza",'utf-8')},
        }
    vatDatasStark.save()
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
    companyDict = create_dict(ResCompany, companyDict, companyName)
    companyDf = pandas.DataFrame(companyDict)
    #Seleziono i dati per l'impresa Servabit
    companyDf = companyDf[companyDf['NAME']==companyName]
    companyDf = companyDf.reset_index(drop=True)
    ResCompanyStark = Stark(companyDf, os.path.join(path, 'COMP.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    ResCompanyStark.VD = {
        'NAME': {'DES': unicode("nome dell'azienda",'utf-8')},
        'TAX': {'DES': unicode("codice fiscale",'utf-8')},
        'VAT': {'DES': unicode("partita iva",'utf-8')},
        'ADDRESS': {'DES': unicode("indirizzo",'utf-8')},
        'CITY': {'DES': unicode("città",'utf-8')},
        'ZIP': {'DES': unicode("cap",'utf-8')},
        'PHONE': {'DES': unicode("telefono",'utf-8')},
        }
    ResCompanyStark.save()
    
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
    invoiceDict = create_dict(invoiceClass, invoiceDict, companyName)
    invoiceDf = pandas.DataFrame(invoiceDict)
    #invoiceDf=invoiceDf[invoiceDf['NAM_IMP']==companyName]
    invoiceStark = Stark(invoiceDf,os.path.join(path, 'INV.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    invoiceStark.VD = {
        'NUM': {'DES': unicode('numero fattura','utf-8')},
        'ESER': {'DES': unicode("nome dell'anno fiscale",'utf-8')},
        'NAM_MOV': {'DES': unicode("nome della scrittura contabile associata",'utf-8')},
        }
    invoiceStark.save()
    
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
    voucherDict = create_dict(voucherClass, voucherDict, companyName)
    voucherDf = pandas.DataFrame(voucherDict)
    #voucherDf=voucherDf[voucherDf['NAM_IMP']==companyName]
    voucherStark = Stark(voucherDf,os.path.join(path, 'VOU.pickle'), TI='elab')
    #effettuo il primo abbellimento di Stark
    voucherStark.VD = {
        'NUM': {'DES': unicode('numero voucher','utf-8')},
        'ESER': {'DES': unicode("nome dell'anno fiscale",'utf-8')},
        'NAM_MOV': {'DES': unicode("nome della scrittura contabile associata",'utf-8')},
        }
    voucherStark.save()

def main():
    configFilePath = os.path.join(BASEPATH,"config","goal2stark.cfg")
    config = Config(configFilePath)
    config.parse()
    companiesNames = config.options.get('companies',False)
    assert(companiesNames)
    companiesNames = companiesNames.split(",")
    picklesPath = config.options.get('pickles_path',False)
    assert(picklesPath)
    immediateVatCreditAccountCode = config.options.get('immediate_credit_vat_account_code',False)
    assert(immediateVatCreditAccountCode)
    immediateVatDebitAccountCode = config.options.get('immediate_debit_vat_account_code',False)
    assert(immediateVatDebitAccountCode)
    deferredVatCreditAccountCode = config.options.get('deferred_credit_vat_account_code',False)
    assert(deferredVatCreditAccountCode)
    deferredVatDebitAccountCode = config.options.get('deferred_debit_vat_account_code',False)
    assert(deferredVatDebitAccountCode)
    treasuryVatAccountCode = config.options.get('treasury_vat_account_code',False)
    assert(treasuryVatAccountCode)
    
    processes = []
    for companyName in companiesNames:
        companyName = companyName.replace(" ","")
        companyProcess = (createDWComp,
                [companyName,picklesPath,immediateVatCreditAccountCode,
                immediateVatDebitAccountCode,deferredVatCreditAccountCode,
                deferredVatDebitAccountCode,treasuryVatAccountCode])
        processes.append(companyProcess)
        
    parallel_jobs.do_jobs_efficiently(processes)

if __name__ == '__main__':
    main()