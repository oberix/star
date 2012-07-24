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
import pandas
import MySQLdb
try:
    import cPickle
except ImportError:
    import Pickle as cPickle

# Servabit libraries
PathPr="/home/contabilita/Star-0.0/ETL/Goal2Stark/"
sys.path.append(PathPr)   
sys.path=list(set(sys.path)) 
import DBmap2
import create_dict
import stark

def ins_blob(company, tip, name, obj):
    dumped = cPickle.dumps(obj, protocol=cPickle.HIGHEST_PROTOCOL)
    c=MySQLdb.connect(host="scoglio.devsite.servabit.it", user = "gigi", passwd="MYSQL.studiabo", db="star")
    cur = c.cursor()
    sql = "INSERT INTO pickles (COMPANY, TYP, NAME, FILE) VALUES (%s, %s, %s, %s)"
    cur.execute(sql, (company, tip, name, dumped))
    c.close()
    
    

def CreateDWComp(Company):
    '''Questa funzione serve a generare per una Comoany i diversi file pickle che compongono il
       Datawarehouse di quella impresa
    ''' 
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
    DIZ_ACC = create_dict.create_dict(ACC, ACCD)
    DF=pandas.DataFrame(DIZ_ACC)
    #Seleziono i dati per l'impresa Servabit
    DF=DF[DF['NAM_IMP']==Company]
    del DF['NAM_IMP']
    del DF['TYP_CON']
    ACC=stark.StarK(DF,TYPE='elab',COD='ACC')
    #effettuo il primo abbellimento di Stark
    ACC.DES['ID0_CON']['DESVAR']=unicode('ID identificativo del conto','utf-8')
    ACC.DES['NAM_CON']['DESVAR']=unicode('Nome descrittivo del conto','utf-8')
    ACC.DES['COD_CON']['DESVAR']=unicode('Codice menorico identificativo del conto','utf-8')
    ACC.DES['GOV_CON']['DESVAR']=unicode('Tipologia che governa la gestione del conto','utf-8')
    ACC.DES['PAN_CON']['DESVAR']=unicode('Nome descrittivo del conto padre','utf-8')
    ACC.DES['PAC_CON']['DESVAR']=unicode('Codice menorico del conto padre','utf-8')
    path='/home/contabilita/Goal-PKL/'+Company
    ACC.DefPathPkl(path)
    ins_blob(Company, 'STK', path+'/ACC.pickle', ACC)
    #ACC.Dumpk('ACC.pickle')

    ############################################################################################
    #  importazione dei dati della classe Account Move Line
    #  contenente le informazioni sulle line di scrittura contabile
    ############################################################################################
    MVLD = {
             'ID0_MVL' : ('id', None), 
             'NAM_MOV' : ('move', ('name', None)), 
             'NAM_MVL' : ('name', None),
             'COD_CON' : ('account', ('code', None)),
             'NAM_IMP'  : ('company', ('name', None)),
             'REF_MVL'  : ('ref', None),
             'DAT_MVL'  : ('date', None),
             'NAM_PRD'  : ('period', ('name', None)),
             'NAM_PAR'  : ('partner', ('name', None)),
             'NAM_CON'  : ('account', ('name', None)),
             'NAM_JRN'  : ('journal', ('name', None)),
             'DBT_MVL'  : ('debit', None),
             'CRT_MVL'  : ('credit', None),
             'STA_MVL'  : ('state', None),
             'NAM_REC'  : ('reconcile', ('name', None)),
             'TAX_COD'  : ('tax_code_id', None), #aggiunto da Nicola il 13/7/2012
             'TAX_AMO'  : ('tax_amount', None), #aggiunto da Nicola il 23/7/2012
             }
    #assegno a MOVL la classe AccountMoveLine
    MVL = DBmap2.AccountMoveLine
    #costruisco il dizionario con le variabili selezionata
    DIZ_MVL = create_dict.create_dict(MVL, MVLD)
    DF=pandas.DataFrame(DIZ_MVL)
    #Seleziono i dati per l'impresa Servabit
    DF=DF[DF['NAM_IMP']==Company]
    del DF['NAM_IMP']
    #del DF['TYP_CON']
    MVL=stark.StarK(DF,TYPE='elab',COD='MVL')
    #effettuo il primo abbellimento di Stark
    MVL.DES['ID0_MVL']['DESVAR']=unicode('ID identificativo della move line','utf-8')
    MVL.DES['NAM_MVL']['DESVAR']=unicode('Nome descrittivo della move line','utf-8')
    MVL.DES['COD_CON']['DESVAR']=unicode('Codice mnemonico identificativo del conto','utf-8')
    MVL.DES['DAT_MVL']['DESVAR']=unicode('data di registrazione','utf-8')
    MVL.DES['STA_MVL']['DESVAR']=unicode('stato della moveline in termini di validazione','utf-8')
    MVL.DES['DBT_MVL']['DESVAR']=unicode('colonna DARE della partita doppia','utf-8')
    MVL.DES['CRT_MVL']['DESVAR']=unicode('colonna AVERE della partita doppia','utf-8')
    MVL.DES['TAX_COD']['DESVAR']=unicode("E' l'identificativo relativo al tax_code",'utf-8') #aggiunto da Nicola il 13/7/2012
    path='/home/contabilita/Goal-PKL/'+Company
    MVL.DefPathPkl(path)
    ins_blob(Company, 'STK', path+'/MVL.pickle', MVL)
    #MVL.Dumpk('MVL.pickle')


############################################################################################
    #  importazione dei dati della classe Account Move 
    #  contenente le informazioni sulle line di scrittura contabile
    ############################################################################################
    MOVD = {
             'ID0_MOL' : ('id', None), 
             'NAM_MOV' : ('name', None), 
             'REF_MOV' : ('ref', None),
             'DAT_MOV' : ('date', None),
             'NAM_PRD'  : ('period', ('name', None)),
             'NAM_JRN'  : ('journal', ('name', None)),
             'TYPE_JRN'  : ('journal', ('type', None)), #aggiunto da Nicola il 23/7/2012
             'NAM_IMP'  : ('company', ('name', None)),
             'NAM_PAR'  : ('partner', ('name', None)),
             'CHK_MOV'  : ('to_check', None),
             'STA_MOV'  : ('state', None),
             'DATE_DOC' : ('invoice', ('date_document', None)), #aggiunto da Nicola il 13/7/2012
             }
    #assegno a MOVL la classe AccountMoveLine
    MOV = DBmap2.AccountMove
    #costruisco il dizionario con le variabili selezionata
    DIZ_MOV = create_dict.create_dict(MOV, MOVD)
    DF=pandas.DataFrame(DIZ_MOV)
    #Seleziono i dati per l'impresa Servabit
    DF=DF[DF['NAM_IMP']==Company]
    del DF['NAM_IMP']
    #del DF['TYP_CON']
    MOV=stark.StarK(DF,TYPE='elab',COD='MOV')
    #effettuo il primo abbellimento di Stark
    MOV.DES['ID0_MOL']['DESVAR']=unicode('ID identificativo della move','utf-8')
    MOV.DES['NAM_MOV']['DESVAR']=unicode('Nome descrittivo della move','utf-8')
    MOV.DES['NAM_PAR']['DESVAR']=unicode('Partner associato alla move','utf-8')
    MOV.DES['DATE_DOC']['DESVAR']=unicode("E' la data della fattura (se la move è associata ad una fattura)",'utf-8')
    path='/home/contabilita/Goal-PKL/'+Company
    MOV.DefPathPkl(path)
    ins_blob(Company, 'STK', path+'/MOV.pickle', MOV)
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
    DIZ_PAR = create_dict.create_dict(PAR, PARD)
    DF=pandas.DataFrame(DIZ_PAR)
    #Seleziono i dati per l'impresa Servabit
    DF=DF[DF['NAM_IMP']==Company]
    del DF['NAM_IMP']
    #del DF['TYP_CON']
    PAR=stark.StarK(DF,TYPE='elab',COD='PAR')
    #effettuo il primo abbellimento di Stark
    PAR.DES['ID0_PAR']['DESVAR']=unicode('ID identificativo del partner','utf-8')
    PAR.DES['NAM_PAR']['DESVAR']=unicode('Nome descrittivo del partner','utf-8')
    PAR.DES['CFS_PAR']['DESVAR']=unicode('Codice fiscale del partner','utf-8')
    PAR.DES['IVA_PAR']['DESVAR']=unicode('Partita IVA del partner','utf-8')
    path='/home/contabilita/Goal-PKL/'+Company
    PAR.DefPathPkl(path)
    ins_blob(Company, 'STK', path+'/PAR.pickle', PAR)
    #PAR.Dumpk('PAR.pickle')
    
    
    ############################################################################################
    #  importazione dei dati della classe Account Tax
    #  contenente le informazioni sulle tasse
    #  aggiunto da Nicola (13-7-2012 ore 9.45)
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
    DIZ_TAX = create_dict.create_dict(TAX, TAX_D)
    DF=pandas.DataFrame(DIZ_TAX)
    #Seleziono i dati per l'impresa Servabit
    DF=DF[DF['NAM_IMP']==Company]
    del DF['NAM_IMP']
    #del DF['TYP_CON']
    TAX=stark.StarK(DF,TYPE='elab',COD='TAX')
    #effettuo il primo abbellimento di Stark
    TAX.DES['NAM_TAX']['DESVAR']=unicode("E' il nome della tassa",'utf-8')
    TAX.DES['TAX_CODE']['DESVAR']=unicode("E' l'identificativo del tax_code di tassa",'utf-8')
    TAX.DES['BASE_CODE']['DESVAR']=unicode("E' l'identificativo del tax_code di imponibile",'utf-8')
    TAX.DES['REF_TAX_CODE']['DESVAR']=unicode("E' l'identificativo del tax_code di tassa (per le note di credito)",'utf-8')
    TAX.DES['REF_BASE_CODE']['DESVAR']=unicode("E' l'identificativo del tax_code di imponibile (per le note di credito)",'utf-8')
    path='/home/contabilita/Goal-PKL/'+Company
    TAX.DefPathPkl(path)
    ins_blob(Company, 'STK', path+'/TAX.pickle', TAX)
    #TAX.Dumpk('TAX.pickle')
