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


'''
funzione per il calcolo dei registri iva
'''
def getVatRegister(picklesPath, companyName, sequenceName, onlyValidatedMoves, periodName=None, fiscalyearName=None):
    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")
    
    companyPathPkl = os.path.join(picklesPath,companyName)
    
    starkTax=StarK.Loadk(companyPathPkl,"TAX.pickle")
    starkMoveLine=StarK.Loadk(companyPathPkl,"MVL.pickle")
    df0 = starkMoveLine.DF
    del df0["ID0_MVL"]
    del df0["CHK_MOV"]
    del df0["NAM_REC"]
    del df0["CRT_MVL"]
    del df0["DBT_MVL"]
    del df0["NAM_CON"]
    del df0["NAM_JRN"]
    del df0["NAM_MVL"]
    del df0["REF_MVL"]
    
    
    df1 = df0.ix[df0['NAM_SEQ']==sequenceName].ix[df0['TAX_COD'].notnull()]
    if periodName:
        df1 = df1.ix[df1['NAM_PRD']==periodName]
    if fiscalyearName:
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


'''
funzione per il calcolo dei riepiloghi iva
'''
def getVatSummary(periodName, picklesPath, companyName, sequenceName, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode):
    df1 = getVatRegister(picklesPath, companyName, sequenceName, onlyValidatedMoves, periodName=periodName)
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
    
    def addTotalRow(df1,detraib=None,immed=None,credit=None):
        df2 = df1
        if detraib is not None:
            df2 = df2.ix[(df2['DETRAIB']==detraib)]
        else:
            df2 = df2.ix[(df2['NAM_TAX']!='Totale')]
            df2['DETRAIB'] = 'Null'
        if immed is not None:
            df2 = df2.ix[(df2['IMMED']==immed)]
        else:
            df2 = df2.ix[(df2['NAM_TAX']!='Totale')]
            df2['IMMED'] = "Null"
        if credit is not None:
            df2 = df2.ix[(df2['CREDIT']==credit)]
        else:
            df2 = df2.ix[(df2['NAM_TAX']!='Totale')]
            df2['CREDIT'] = "Null"
        del df2['NAM_TAX']
        groupbyCols = list(df2.columns)
        groupbyCols.remove('BASE')
        groupbyCols.remove('TAX')
        df2 = df2.groupby(groupbyCols).sum()[['BASE','TAX']].reset_index()
        df2['NAM_TAX'] = "Totale"
        df1 = pandas.concat([df1,df2])
        df1 = df1.reset_index(drop=True)
        return df1
    
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

'''
funzione che restituisce l'iva differita o da pagare per il periodo (o l'anno fiscale) passati come parametro
se searchPayments è True, si stanno cercando le fatture che sono state pagate nel periodo (o anno fiscale)
se searchPayments è False, si stanno cercando le fatture che non sono state ancora pagate entro il periodo (o anno fiscale)
'''
def getDeferredVatDetail(picklesPath, companyName, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode, searchPayments=False, periodName=None, fiscalyearName=None):
    if not periodName and not fiscalyearName:
        raise RuntimeError("Errore: i parametri periodName e fiscalyearName non devono essere entrambi nulli")
    
    companyPathPkl = os.path.join(picklesPath,companyName)
    
    starkTax=StarK.Loadk(companyPathPkl,"TAX.pickle")
    starkMoveLine=StarK.Loadk(companyPathPkl,"MVL.pickle")
    starkPeriod=StarK.Loadk(companyPathPkl,"PERIOD.pickle")
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
        df2 = df1.ix[df1['NAM_REC'].notnull()]
        dfWithPayments = None
        if periodName:
            dfWithPayments = df2.ix[df0['NAM_PRD']==periodName]
        else:
            dfWithPayments = df2.ix[df0['NAM_FY']==fiscalyearName]
        dfWithPayments = dfWithPayments.ix[
            ((dfWithPayments['COD_CON']==deferredVatCreditAccountCode) & (dfWithPayments['CRT_MVL']>0)) | 
            ((dfWithPayments['COD_CON']==deferredVatDebitAccountCode) & (dfWithPayments['DBT_MVL']>0))
            ]
        dfWithoutPayments = df2.ix[
            ((df2['COD_CON']==deferredVatCreditAccountCode) & (df2['DBT_MVL']>0)) |
            ((df2['COD_CON']==deferredVatDebitAccountCode) & (df2['CRT_MVL']>0))
            ]
        dfWithPayments = dfWithPayments[['NAM_REC','DAT_MVL']]
        dfWithPayments = dfWithPayments.rename(columns={'DAT_MVL' : 'DAT_PAY'})
        dfWithoutPayments['AMO'] = dfWithoutPayments['DBT_MVL']
        dfWithoutPayments['AMO'].ix[dfWithoutPayments['AMO']==0] = dfWithoutPayments['CRT_MVL']
        dfWithoutPayments = dfWithoutPayments[['DAT_MVL','NAM_PAR','AMO','NAM_TAX','NAM_MOV','NAM_SEQ','NAM_REC']]
        df2 = pandas.merge(dfWithPayments,dfWithoutPayments,on='NAM_REC')
        del df2['NAM_REC']
    #else: si stanno cercando le fatture con esigibilità differita non ancora pagate
    else:
        df2 = df1.ix[df1['NAM_REC'].isnull()]
        xxxxxx
        
        print starkPeriod.DF
        dfWithoutPayments = dfWithoutPayments.ix[dfWithoutPayments['NAM_REC'].isnull()]
        print dfWithoutPayments
        
    return df2
    

def getDeferredVatSummaryLines(session, company_id, sequence_names, payment_period_ids, search_period_ids, onlyValidatedMoves, deferred_credit_account_code, deferred_debit_account_code):
    '''
    the summary considers the deferred vat moves belonging to search_period_ids and that have been payed in payment_period_ids and the deferred vat moves belonging to search_period_ids and that have not been payed in search_period_ids
    @returns : a dictionary with two keys: 'sequences' and 'totals'. 'sequences' will be a list of dictionaries (one for each sequence). 'totals' will be a dictionary with totals values
    '''
    results={}
    
    payment_lines=getDeferredVatDetailLines(session,company_id, True, payment_period_ids, search_period_ids, onlyValidatedMoves, deferred_credit_account_code,deferred_debit_account_code)
    not_payment_lines=getDeferredVatDetailLines(session,company_id, False, search_period_ids, search_period_ids, onlyValidatedMoves, deferred_credit_account_code,deferred_debit_account_code)
    
    tax_code_ids=[]
    for line in payment_lines:
        if tax_code_ids.count(line['tax_code_id'])==0:
            tax_code_ids.append(line['tax_code_id'])                
    for line in not_payment_lines:
        if tax_code_ids.count(line['tax_code_id'])==0:
            tax_code_ids.append(line['tax_code_id'])
    
    debit_vat_now_exigible_taxable_total=Decimal('0.00')
    debit_vat_now_exigible_tax_total=Decimal('0.00')
    credit_vat_now_exigible_taxable_total=Decimal('0.00')
    credit_vat_now_exigible_tax_total=Decimal('0.00')
    debit_vat_not_exigible_taxable_total=Decimal('0.00')
    debit_vat_not_exigible_tax_total=Decimal('0.00')
    credit_vat_not_exigible_taxable_total=Decimal('0.00')
    credit_vat_not_exigible_tax_total=Decimal('0.00')
    
    result_sequences=[]
    sequences=session.query(IrSequence).filter(IrSequence.name.in_(sequence_names)).all()
    for vat_sequence in sequences:
        sequence_taxes=[]
        
        sequence_debit_vat_now_exigible_taxable_total=Decimal('0.00')
        sequence_debit_vat_now_exigible_tax_total=Decimal('0.00')
        sequence_credit_vat_now_exigible_taxable_total=Decimal('0.00')
        sequence_credit_vat_now_exigible_tax_total=Decimal('0.00')
        sequence_debit_vat_not_exigible_taxable_total=Decimal('0.00')
        sequence_debit_vat_not_exigible_tax_total=Decimal('0.00')
        sequence_credit_vat_not_exigible_taxable_total=Decimal('0.00')
        sequence_credit_vat_not_exigible_tax_total=Decimal('0.00')
        
        for tax_code_id in tax_code_ids:
            payments_taxable_amount=Decimal('0.00')
            payments_tax_amount=Decimal('0.00')
            not_payments_taxable_amount=Decimal('0.00')
            not_payments_tax_amount=Decimal('0.00')
            
            tax_name=False
            
            for line in payment_lines:                    
                if tax_code_id==line['tax_code_id'] and vat_sequence.name==line['vat_register']:
                    payments_taxable_amount+=line['taxable_amount']
                    payments_tax_amount+=line['tax_amount']
                    if not tax_name:
                        tax_name=line['tax_name']
                        
                    if line['account_code']==deferred_credit_account_code:
                        sequence_credit_vat_now_exigible_taxable_total+=line['taxable_amount']
                        sequence_credit_vat_now_exigible_tax_total+=line['tax_amount']
                    else:
                        sequence_debit_vat_now_exigible_taxable_total+=line['taxable_amount']
                        sequence_debit_vat_now_exigible_tax_total+=line['tax_amount']
                    
            for line in not_payment_lines:
                if tax_code_id==line['tax_code_id'] and vat_sequence.name==line['vat_register']:
                    not_payments_taxable_amount+=line['taxable_amount']
                    not_payments_tax_amount+=line['tax_amount']
                    if not tax_name:
                        tax_name=line['tax_name']
                        
                    if line['account_code']==deferred_credit_account_code:
                        sequence_credit_vat_not_exigible_taxable_total+=line['taxable_amount']
                        sequence_credit_vat_not_exigible_tax_total+=line['tax_amount']
                    else:
                        sequence_debit_vat_not_exigible_taxable_total+=line['taxable_amount']
                        sequence_debit_vat_not_exigible_tax_total+=line['tax_amount']
                    
            if payments_taxable_amount!=Decimal('0.00') or not_payments_taxable_amount!=Decimal('0.00'):
                tax_data={
                    'tax_name': tax_name,
                    'payments_taxable_amount': payments_taxable_amount,
                    'payments_tax_amount': payments_tax_amount,
                    'not_payments_taxable_amount': not_payments_taxable_amount,
                    'not_payments_tax_amount': not_payments_tax_amount,
                    }
                sequence_taxes.append(tax_data)
                
        
        paid_or_received_totals={
            'debit_taxable_amount': sequence_debit_vat_now_exigible_taxable_total,
            'debit_tax_amount': sequence_debit_vat_now_exigible_tax_total,
            'credit_taxable_amount': sequence_credit_vat_now_exigible_taxable_total,
            'credit_tax_amount': sequence_credit_vat_now_exigible_tax_total,
            }
        
        to_pay_or_to_receive_totals={
            'debit_taxable_amount': sequence_debit_vat_not_exigible_taxable_total,
            'debit_tax_amount': sequence_debit_vat_not_exigible_tax_total,
            'credit_taxable_amount': sequence_credit_vat_not_exigible_taxable_total,
            'credit_tax_amount': sequence_credit_vat_not_exigible_tax_total,
            }
        
        result_sequences.append({
            vat_sequence.name : {
                'taxes': sequence_taxes,
                'paid_received_totals': paid_or_received_totals,
                'pay_receive_totals': to_pay_or_to_receive_totals,
                },
            })
        
        debit_vat_now_exigible_taxable_total+=sequence_debit_vat_now_exigible_taxable_total
        debit_vat_now_exigible_tax_total+=sequence_debit_vat_now_exigible_tax_total
        credit_vat_now_exigible_taxable_total+=sequence_credit_vat_now_exigible_taxable_total
        credit_vat_now_exigible_tax_total+=sequence_credit_vat_now_exigible_tax_total
        debit_vat_not_exigible_taxable_total+=sequence_debit_vat_not_exigible_taxable_total
        debit_vat_not_exigible_tax_total+=sequence_debit_vat_not_exigible_tax_total
        credit_vat_not_exigible_taxable_total+=sequence_credit_vat_not_exigible_taxable_total
        credit_vat_not_exigible_tax_total+=sequence_credit_vat_not_exigible_tax_total
    
    results['sequences']=result_sequences
    
    #build 'totals' value
    to_pay_or_to_receive_totals={
        'debit_taxable_amount': debit_vat_not_exigible_taxable_total,
        'debit_tax_amount': debit_vat_not_exigible_tax_total,
        'credit_taxable_amount': credit_vat_not_exigible_taxable_total,
        'credit_tax_amount': credit_vat_not_exigible_tax_total,
        }
    results['pay_receive_totals']=to_pay_or_to_receive_totals
    
    paid_or_received_totals={
        'debit_taxable_amount': debit_vat_now_exigible_taxable_total,
        'debit_tax_amount': debit_vat_now_exigible_tax_total,
        'credit_taxable_amount': credit_vat_now_exigible_taxable_total,
        'credit_tax_amount': credit_vat_now_exigible_tax_total,
        }    
    results['paid_received_totals']=paid_or_received_totals
        
    return results


def getLiquidationSummaryFinalLines(session, due_or_credit_vat, company_id, period_id, treasury_vat_account_code, dict_results={}, onlyValidatedMoves=True):
    period=session.query(AccountPeriod).filter(AccountPeriod.id==period_id).first()
    
    vat_in_the_period={}
    if due_or_credit_vat<=0:     
        vat_in_the_period['credit']=-due_or_credit_vat
    else:
        vat_in_the_period['debit']=due_or_credit_vat
    dict_results['vat_in_the_period']=vat_in_the_period
    
    treasury_vat_account=session.query(AccountAccount).filter(AccountAccount.code==treasury_vat_account_code,AccountAccount.company_id==company_id).first()
    treasury_vat_account_totals=AccountAccount.computeAmount(AccountAccount, session, treasury_vat_account, ['debit','credit'], period.fiscalyear.date_start, period.date_stop, onlyValidatedMoves)
    treasury_vat_account_balance=Decimal('0.00')
    treasury_vat_account_balance+=treasury_vat_account_totals['debit']
    treasury_vat_account_balance-=treasury_vat_account_totals['credit']
    
    previous_period_results={}
    if treasury_vat_account_balance>0:
        previous_period_results['debit']=treasury_vat_account_balance
    else:
        previous_period_results['credit']=-treasury_vat_account_balance
    due_or_credit_vat+=treasury_vat_account_balance
    dict_results['previous_period_results']=previous_period_results
    
    
    due_or_credit_vat_dict={}
    if due_or_credit_vat>=0:
        due_or_credit_vat_dict['debit']=due_or_credit_vat
    else:
        due_or_credit_vat_dict['credit']=-due_or_credit_vat
    dict_results['due_or_credit_vat']=due_or_credit_vat_dict
    
    if len(period.fiscalyear.periods)==4 and due_or_credit_vat>0:
        interests=(due_or_credit_vat/Decimal(100)).quantize(Decimal('.01'))
        
        interests_dict={
            'debit' : interests
            }
        dict_results['interests']=interests_dict
    
        due_or_credit_vat_with_interest={
            'debit' : due_or_credit_vat+interests,
            }
        dict_results['due_or_credit_vat_with_interest']=due_or_credit_vat_with_interest
    
    return dict_results


def getVatLiquidationSummaryLines(session, period_id, company_id, onlyValidatedMoves, immediate_vat_credit_account_code, immediate_vat_debit_account_code, deferred_vat_credit_account_code, deferred_vat_debit_account_code, treasury_vat_account_code):
    results={}
    
    sequence_names=_getVatSequenceNames(session, company_id)
    
    #calculate immediate vat lines
    credit_vat_total=Decimal('0.00')
    debit_vat_total=Decimal('0.00')
    immediate_vat_amounts=[]
    for sequence_name in sequence_names:
        vat_summary_results=getVatSummaryResults(session, False, [period_id], company_id, sequence_name, onlyValidatedMoves, immediate_vat_credit_account_code, immediate_vat_debit_account_code, deferred_vat_credit_account_code, deferred_vat_debit_account_code)
        immediate_total=vat_summary_results.get('immediate_total',False)
        if immediate_total:
            immediate_vat_amounts.append({
                'sequence_name': sequence_name,
                'debit': immediate_total['debit_tax_amount'],
                'credit': immediate_total['credit_tax_amount'],
                })
            credit_vat_total+=immediate_total['credit_tax_amount']
            debit_vat_total+=immediate_total['debit_tax_amount']
    results['immediate_vat_amounts']=immediate_vat_amounts
    
    deferred_credit_vat_total=Decimal('0.00')
    deferred_debit_vat_total=Decimal('0.00')
    search_period_ids=AccountPeriod.getPreviousPeriodIdsUntilXyears(AccountPeriod,session,period_id,2,company_id)
    search_period_ids.append(period_id)
    deferred_vat_summary_results=getDeferredVatSummaryLines(session, company_id, sequence_names, [period_id], search_period_ids, onlyValidatedMoves, deferred_vat_credit_account_code, deferred_vat_debit_account_code)
    deferred_vat_amounts={
        'debit': deferred_vat_summary_results['paid_received_totals']['debit_tax_amount'],
        'credit': deferred_vat_summary_results['paid_received_totals']['credit_tax_amount'],
        }
    deferred_credit_vat_total+=deferred_vat_amounts['credit']
    deferred_debit_vat_total+=deferred_vat_amounts['debit']
    results['deferred_vat_amounts']=deferred_vat_amounts

    debit_sum=debit_vat_total+deferred_debit_vat_total
    credit_sum=credit_vat_total+deferred_credit_vat_total
    vat_totals_amounts={
        'debit': debit_sum,
        'credit': credit_sum,
        }
    results['vat_totals_amounts']=vat_totals_amounts
    
    due_or_credit_vat=debit_sum-credit_sum
    
    final_lines=getLiquidationSummaryFinalLines(session, due_or_credit_vat, company_id, period_id, treasury_vat_account_code, dict_results=results, onlyValidatedMoves=onlyValidatedMoves)
    
    return results
    
def getControlSummaryVatLines(session, vatSummaryResults, sequence_names, company_id, fiscalyear_id, onlyValidatedMoves, immediate_vat_credit_account_code, immediate_vat_debit_account_code, deferred_vat_credit_account_code, deferred_vat_debit_account_code):
    results={}
    
    immediate_vat_total_line=vatSummaryResults['immediate_total']
    deferred_vat_total_line=vatSummaryResults['deferred_total']
        
    credit_vat_now_exigible_taxable_amount_from_previous_exercise=Decimal('0.00')
    credit_vat_now_exigible_tax_amount_from_previous_exercise=Decimal('0.00')
    debit_vat_now_exigible_taxable_amount_from_previous_exercise=Decimal('0.00')
    debit_vat_now_exigible_tax_amount_from_previous_exercise=Decimal('0.00')
        
    period_ids=[]
    fiscalyear=session.query(AccountFiscalyear).filter(AccountFiscalyear.id==fiscalyear_id).first()
    if fiscalyear:
        for p in fiscalyear.periods:
            period_ids.append(p.id)
    year_before=AccountFiscalyear.findYearBefore(AccountFiscalyear,session,fiscalyear_id)
    credit_line=False
    debit_line=False
    if year_before:
        periods_before=session.query(AccountPeriod).filter(AccountPeriod.fiscalyear_id==year_before.id).all()
        periods_before_ids=[]
        for p in periods_before:
            periods_before_ids.append(p.id)
        
        deferred_summary_results=getDeferredVatSummaryLines(session, company_id, sequence_names, period_ids, periods_before_ids, onlyValidatedMoves, deferred_vat_credit_account_code, deferred_vat_debit_account_code)
        for sequence in deferred_summary_results['sequences']:
            sequence_name=sequence.keys()[0]
            if sequence_names.count(sequence_name)>0:
                debit_vat_now_exigible_taxable_amount_from_previous_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['debit_taxable_amount']
                debit_vat_now_exigible_tax_amount_from_previous_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['debit_tax_amount']
                credit_vat_now_exigible_taxable_amount_from_previous_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['credit_taxable_amount']
                credit_vat_now_exigible_tax_amount_from_previous_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['credit_tax_amount']
                
    #append deferred vat now exigible from previous exercise
    previous_exercise_deferred_vat_now_exigible_amounts={
        'debit_taxable': debit_vat_now_exigible_taxable_amount_from_previous_exercise,
        'debit_tax': debit_vat_now_exigible_tax_amount_from_previous_exercise,
        'credit_taxable': credit_vat_now_exigible_taxable_amount_from_previous_exercise,
        'credit_tax': credit_vat_now_exigible_tax_amount_from_previous_exercise,
        }
    results['previous_exercise_deferred_vat_now_exigible_amounts']=previous_exercise_deferred_vat_now_exigible_amounts
    
        
    credit_vat_now_exigible_taxable_amount_current_exercise=Decimal('0.00')
    credit_vat_now_exigible_tax_amount_current_exercise=Decimal('0.00')
    debit_vat_now_exigible_taxable_amount_current_exercise=Decimal('0.00')
    debit_vat_now_exigible_tax_amount_current_exercise=Decimal('0.00')
        
    deferred_summary_results=getDeferredVatSummaryLines(session, company_id, sequence_names, period_ids, period_ids, onlyValidatedMoves, deferred_vat_credit_account_code, deferred_vat_debit_account_code)
    for sequence in deferred_summary_results['sequences']:
        sequence_name=sequence.keys()[0]
        if sequence_names.count(sequence_name)>0:
            debit_vat_now_exigible_taxable_amount_current_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['debit_taxable_amount']
            debit_vat_now_exigible_tax_amount_current_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['debit_tax_amount']
            credit_vat_now_exigible_taxable_amount_current_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['credit_taxable_amount']
            credit_vat_now_exigible_tax_amount_current_exercise+=sequence[sequence.keys()[0]]['paid_received_totals']['credit_tax_amount']
    
    current_exercise_deferred_vat_now_exigible_amounts={
        'debit_taxable': debit_vat_now_exigible_taxable_amount_current_exercise,
        'debit_tax': debit_vat_now_exigible_tax_amount_current_exercise,
        'credit_taxable': credit_vat_now_exigible_taxable_amount_current_exercise,
        'credit_tax': credit_vat_now_exigible_tax_amount_current_exercise,
        }
    results['current_exercise_deferred_vat_now_exigible_amounts']=current_exercise_deferred_vat_now_exigible_amounts
    
    deferred_vat_now_exigible_total_amounts={
        'debit_taxable': debit_vat_now_exigible_taxable_amount_current_exercise+debit_vat_now_exigible_taxable_amount_from_previous_exercise,
        'debit_tax': debit_vat_now_exigible_tax_amount_current_exercise+debit_vat_now_exigible_tax_amount_from_previous_exercise,
        'credit_taxable': credit_vat_now_exigible_taxable_amount_current_exercise+credit_vat_now_exigible_taxable_amount_from_previous_exercise,
        'credit_tax': credit_vat_now_exigible_tax_amount_current_exercise+credit_vat_now_exigible_tax_amount_from_previous_exercise,
        }
    results['deferred_vat_now_exigible_total_amounts']=deferred_vat_now_exigible_total_amounts
    
    vat_now_exigible_total_amounts={
        'debit_taxable': deferred_vat_now_exigible_total_amounts['debit_taxable']+immediate_vat_total_line['debit_taxable_amount'],
        'debit_tax': deferred_vat_now_exigible_total_amounts['debit_tax']+immediate_vat_total_line['debit_tax_amount'],
        'credit_taxable': deferred_vat_now_exigible_total_amounts['credit_taxable']+immediate_vat_total_line['credit_taxable_amount'],
        'credit_tax': deferred_vat_now_exigible_total_amounts['credit_tax']+immediate_vat_total_line['credit_tax_amount'],
        }
    results['vat_now_exigible_total_amounts']=vat_now_exigible_total_amounts
    
    deferred_vat_to_require_in_next_exercise={
        'debit_taxable': deferred_vat_total_line['debit_taxable_amount']-debit_vat_now_exigible_taxable_amount_current_exercise,
        'debit_tax': deferred_vat_total_line['debit_tax_amount']-debit_vat_now_exigible_tax_amount_current_exercise,
        'credit_taxable': deferred_vat_total_line['credit_taxable_amount']-credit_vat_now_exigible_taxable_amount_current_exercise,
        'credit_tax': deferred_vat_total_line['credit_tax_amount']-credit_vat_now_exigible_tax_amount_current_exercise,
        }
    results['deferred_vat_to_require_in_next_exercise']=deferred_vat_to_require_in_next_exercise

    return results
