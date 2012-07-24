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
from decimal import Decimal

'''
funzione per il calcolo dei registri iva
'''
def getVatRegisterLines(companyName, sequenceNames, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, periodName=None, fiscalyearName=None):
    lines=[]
    
    if type(periodIds) is int:
        periodIds=[periodIds]
    
    #get journal ids
    sequences=session.query(IrSequence).filter(IrSequence.name.in_(sequenceNames),IrSequence.company_id==companyId).all()
    if not sequences:
        raise RuntimeError('there are not '+str(sequenceNames)+' sequences for company with id='+str(companyId))
    journalIds=[]
    for seq in sequences:
        for journal in seq.journals:
            journalIds.append(journal.id)
    
    #get moves
    moves=[]
    if onlyValidatedMoves:
        moves=session.query(AccountMove).filter(
                                    AccountMove.company_id==companyId,
                                    AccountMove.journal_id.in_(journalIds),
                                    AccountMove.state=='posted',
                                    AccountMove.period_id.in_(periodIds)
                                    ).\
                                    order_by(AccountMove.date,AccountMove.id).all()
    else:
        moves=session.query(AccountMove).filter(
                                    AccountMove.company_id==companyId,
                                    AccountMove.journal_id.in_(journalIds),
                                    AccountMove.period_id.in_(periodIds)
                                    ).\
                                    order_by(AccountMove.date,AccountMove.id).all()
    
    #for each move
    processedMoves=[]
    for move in moves:
        isTaxMove=False
        
        for ml in move.move_lines:
            if ml.tax_code_id:
                isTaxMove=True
                isTaxAmountMl=False
                isRefundTax=(ml.journal.type=='sale_refund' or ml.journal.type=='purchase_refund')
                tax=False                    
                if not isRefundTax:
                    tax=session.query(AccountTax).filter(AccountTax.tax_code_id==ml.tax_code_id).first()
                else:
                    tax=session.query(AccountTax).filter(AccountTax.ref_tax_code_id==ml.tax_code_id).first()
                if tax:
                    #verify if the vat is immediate or deferred and if is not deductible
                    #immediate_vat=True
                    #not_deductible_tax=True
                    #if ml.account_id.code==deferredVatCreditAccountCode or ml.account_id.code==deferredVatDebitAccountCode:
                        #immediate_vat=False
                        #not_deductible_tax=False
                    #if ml.account_id.code==immediateVatCreditAccountCode or ml.account_id.code==immediateVatDebitAccountCode:
                        #not_deductible_tax=False
                    
                    baseCodeId=False
                    if not isRefundTax:
                        baseCodeId=tax.base_code_id
                    else:
                        baseCodeId=tax.ref_base_code_id
                        
                    taxable_amount=Decimal('0.00')
                    for ml2 in move.move_lines:
                        if ml2.tax_code_id==baseCodeId:
                            taxable_amount+=ml2.tax_amount
                            
                    #create report line data
                    reportLineData={}                        
                    #if the move has not already been processed
                    if(processedMoves.count(move.id)==0):
                        processedMoves.append(move.id)
                    
                        moveNameSplits=move.name.split("/")
                        reportLineData['protocol_number']=moveNameSplits[len(moveNameSplits)-1]
                        reportLineData['partner_name']=move.partner.name
                        reportLineData['reference']=move.ref
                        
                        document_date=move._get_date_document().strftime("%d-%m-%Y")
                        reportLineData['document_date']=document_date
                        
                        date_registration=move.date.strftime("%d-%m-%Y")
                        reportLineData['date_registration']=date_registration         
                    else:
                        reportLineData['protocol_number']=""
                        reportLineData['partner_name']=""
                        reportLineData['reference']=""
                        reportLineData['document_date']=""
                        reportLineData['date_registration']=""
                        
                    reportLineData['tax_name']=ml.name
                    reportLineData['taxable_amount']=taxable_amount
                    reportLineData['tax_amount']=ml.tax_amount
                    #reportLineData['immediate_vat']=immediate_vat
                    #reportLineData['not_deductible_tax']=not_deductible_tax
                    reportLineData['account_code']=ml.account.code
                    reportLineData['tax_code_id']=tax.tax_code_id
                    lines.append(reportLineData)
    
        if not isTaxMove:
            reportLineData={}
            processedMoves.append(move.id)
            
            moveNameSplits=move.name.split("/")
            reportLineData['protocol_number']=moveNameSplits[len(moveNameSplits)-1]
            if move.partner:
                reportLineData['partner_name']=move.partner.name
            else:
                reportLineData['partner_name']='N.D.'
            reportLineData['reference']=move.ref
            
            document_date=move._get_date_document()
            if document_date:
                document_date=document_date.strftime("%d-%m-%Y")
            reportLineData['document_date']=document_date
            
            date_registration=move.date.strftime("%d-%m-%Y")
            reportLineData['date_registration']=date_registration
            
            reportLineData['tax_name']='N.D.'
            reportLineData['taxable_amount']='N.D.'
            reportLineData['tax_amount']='N.D.'
            lines.append(reportLineData)
    
    return lines

#calculate amounts aggregating by tax_code_id (field id of tax.code object) and code of the account
def _getPeriodsAmounts(vat_register_lines):
    amounts={}
    for line in vat_register_lines:
        tax_code_id=line.get('tax_code_id',False)
        account_code=line.get('account_code',False)
        if tax_code_id and account_code:
            previous_vals=amounts.get((tax_code_id,account_code),False)
            if previous_vals:
                taxable_amount=previous_vals['taxable_amount']
                tax_amount=previous_vals['tax_amount']
                taxable_amount+=line['taxable_amount']
                tax_amount+=line['tax_amount']
                previous_vals['taxable_amount']=taxable_amount
                previous_vals['tax_amount']=tax_amount
                amounts[(tax_code_id,account_code)]=previous_vals
            else:
                amounts[(tax_code_id,account_code)]={
                    'tax_name' : line['tax_name'],
                    'taxable_amount' : line['taxable_amount'],
                    'tax_amount' : line['tax_amount'],
                    'account_code' : line['account_code'],
                    }
    return amounts

'''
funzione per il calcolo dei riepiloghi iva
'''
def getVatSummaryResults(session, vat_register_lines, period_ids, company_id, sequence_names, onlyValidatedMoves, immediate_vat_credit_account_code, immediate_vat_debit_account_code, deferred_vat_credit_account_code, deferred_vat_debit_account_code):
    result={}
    
    if type(sequence_names)==str or type(sequence_names)==unicode:
        sequence_names=[sequence_names]
    if not vat_register_lines:
        vat_register_lines=getVatRegisterLines(session,period_ids,company_id,sequence_names,onlyValidatedMoves,immediate_vat_credit_account_code,immediate_vat_debit_account_code,deferred_vat_credit_account_code,deferred_vat_debit_account_code)
    
    #calculate amounts in the period
    amounts_in_the_period=_getPeriodsAmounts(vat_register_lines)
    
    immediate_taxes_summary_lines=[]
    deferred_taxes_summary_lines=[]
    not_deductible_taxes_summary_lines=[]
    
    immediate_period_credit_taxable_amount=Decimal('0.00')
    immediate_period_credit_tax_amount=Decimal('0.00')
    immediate_period_debit_taxable_amount=Decimal('0.00')
    immediate_period_debit_tax_amount=Decimal('0.00')
    deferred_period_credit_taxable_amount=Decimal('0.00')
    deferred_period_credit_tax_amount=Decimal('0.00')
    deferred_period_debit_taxable_amount=Decimal('0.00')
    deferred_period_debit_tax_amount=Decimal('0.00')
    not_deductible_period_credit_taxable_amount=Decimal('0.00')
    not_deductible_period_credit_tax_amount=Decimal('0.00')
    
    for el in amounts_in_the_period:
        report_line={
            'tax': '',
            'credit_taxable_amount': '',
            'credit_tax_amount' : '',
            'debit_taxable_amount': '',
            'debit_tax_amount': '',
            }
        
        period_amounts=amounts_in_the_period[el]
        if period_amounts['account_code']==immediate_vat_credit_account_code:
            report_line['tax']=period_amounts['tax_name']
            report_line['credit_taxable_amount']=period_amounts['taxable_amount']
            report_line['credit_tax_amount']=period_amounts['tax_amount']
            immediate_period_credit_taxable_amount+=period_amounts['taxable_amount']
            immediate_period_credit_tax_amount+=period_amounts['tax_amount']
            immediate_taxes_summary_lines.append(report_line)
        elif period_amounts['account_code']==immediate_vat_debit_account_code:
            report_line['tax']=period_amounts['tax_name']
            report_line['debit_taxable_amount']=period_amounts['taxable_amount']
            report_line['debit_tax_amount']=period_amounts['tax_amount']
            immediate_period_debit_taxable_amount+=period_amounts['taxable_amount']
            immediate_period_debit_tax_amount+=period_amounts['tax_amount']
            immediate_taxes_summary_lines.append(report_line)
        elif period_amounts['account_code']==deferred_vat_credit_account_code:
            report_line['tax']=period_amounts['tax_name']
            report_line['credit_taxable_amount']=period_amounts['taxable_amount']
            report_line['credit_tax_amount']=period_amounts['tax_amount']
            deferred_period_credit_taxable_amount+=period_amounts['taxable_amount']
            deferred_period_credit_tax_amount+=period_amounts['tax_amount']
            deferred_taxes_summary_lines.append(report_line)
        elif period_amounts['account_code']==deferred_vat_debit_account_code:
            report_line['tax']=period_amounts['tax_name']
            report_line['debit_taxable_amount']=period_amounts['taxable_amount']
            report_line['debit_tax_amount']=period_amounts['tax_amount']
            deferred_period_debit_taxable_amount+=period_amounts['taxable_amount']
            deferred_period_debit_tax_amount+=period_amounts['tax_amount']
            deferred_taxes_summary_lines.append(report_line)
        #otherwise it's a undeductible amounts object
        else:
            report_line['tax']=period_amounts['tax_name']
            report_line['credit_taxable_amount']=period_amounts['taxable_amount']
            report_line['credit_tax_amount']=period_amounts['tax_amount']
            not_deductible_period_credit_taxable_amount+=period_amounts['taxable_amount']
            not_deductible_period_credit_tax_amount+=period_amounts['tax_amount']
            not_deductible_taxes_summary_lines.append(report_line)
    
    result['immediate_lines']=immediate_taxes_summary_lines
    result['deferred_lines']=deferred_taxes_summary_lines
    result['undeductible_lines']=not_deductible_taxes_summary_lines
    
    if len(not_deductible_taxes_summary_lines)+len(deferred_taxes_summary_lines)+len(immediate_taxes_summary_lines)>0:
        result['immediate_total']={
            'credit_taxable_amount':immediate_period_credit_taxable_amount,
            'credit_tax_amount' : immediate_period_credit_tax_amount,
            'debit_taxable_amount': immediate_period_debit_taxable_amount,
            'debit_tax_amount': immediate_period_debit_tax_amount,
        }
    
        result['deferred_total']={
            'credit_taxable_amount':deferred_period_credit_taxable_amount,
            'credit_tax_amount' : deferred_period_credit_tax_amount,
            'debit_taxable_amount': deferred_period_debit_taxable_amount,
            'debit_tax_amount': deferred_period_debit_tax_amount,
        }
        
        result['deductible_total']={
            'credit_taxable_amount': immediate_period_credit_taxable_amount+deferred_period_credit_taxable_amount,
            'credit_tax_amount' : immediate_period_credit_tax_amount+deferred_period_credit_tax_amount,
            'debit_taxable_amount': immediate_period_debit_taxable_amount+deferred_period_debit_taxable_amount,
            'debit_tax_amount': immediate_period_debit_tax_amount+deferred_period_debit_tax_amount,
        }
        
        result['undeductible_total']={
            'credit_taxable_amount':not_deductible_period_credit_taxable_amount,
            'credit_tax_amount' : not_deductible_period_credit_tax_amount,
        }
        
        result['deductible_plus_undeductible_total']={
            'credit_taxable_amount': immediate_period_credit_taxable_amount+deferred_period_credit_taxable_amount+not_deductible_period_credit_taxable_amount,
            'credit_tax_amount' : immediate_period_credit_tax_amount+deferred_period_credit_tax_amount+not_deductible_period_credit_tax_amount,
            'debit_taxable_amount': immediate_period_debit_taxable_amount+deferred_period_debit_taxable_amount,
            'debit_tax_amount': immediate_period_debit_tax_amount+deferred_period_debit_tax_amount,
        }
    
    return result

def _getVatSequenceIds(session,company_id):
    sequences=session.query(IrSequence).filter(IrSequence.code=='RIVA',IrSequence.company_id==company_id).all()
    sequencesIds=[]
    for s in sequences:
        sequencesIds.append(s.id)
    if len(sequencesIds)==0:
        raise RuntimeError('there are not vat sequences for company with id='+str(company_id)+". Please configure vat sequences.")
    return sequencesIds
    
def _getVatSequenceNames(session,company_id):
    sequences=session.query(IrSequence).filter(IrSequence.code=='RIVA',IrSequence.company_id==company_id).all()
    sequenceNames=[]
    for s in sequences:
        sequenceNames.append(s.name)
    if len(sequenceNames)==0:
        raise RuntimeError('there are not vat sequences for company with id='+str(company_id)+". Please configure vat sequences.")
    return sequenceNames

'''
method called for getting deferred vat payed or to pay in periods passed as argument.
if get_payments flag is True, you're looking for deferred vat moves in search_period_ids, that have been payed in payment_period_ids
if get_payments flag is False, you're looking for deferred vat moves in search_period_ids, that have not been payed in payment_period_ids
'''
def getDeferredVatDetailLines(session, company_id, get_payments, payment_period_ids, search_period_ids, onlyValidatedMoves, deferred_credit_account_code, deferred_debit_account_code):
    
    vat_sequence_ids=_getVatSequenceIds(session,company_id)
    vat_journals=session.query(AccountJournal).filter(AccountJournal.sequence_id.in_(vat_sequence_ids)).all()
    vat_journal_ids=[]
    for j in vat_journals:
        vat_journal_ids.append(j.id)
    
    debit_deferred_move_line_ids=[]
    credit_deferred_move_line_ids=[]
    
    deferred_move_lines=[]
    if onlyValidatedMoves:
        deferred_move_lines=session.query(AccountMoveLine).filter(
                                                AccountMoveLine.move.has(state='posted'),
                                                AccountMoveLine.company_id==company_id,
                                                AccountMoveLine.account.has(code=deferred_debit_account_code),
                                                AccountMoveLine.period_id.in_(search_period_ids),
                                                AccountMoveLine.journal_id.in_(vat_journal_ids),
                                                ).order_by(AccountMoveLine.date).all()
        deferred_move_lines.extend(session.query(AccountMoveLine).filter(
                                        AccountMoveLine.move.has(state='posted'),
                                        AccountMoveLine.company_id==company_id,
                                        AccountMoveLine.account.has(code=deferred_credit_account_code),
                                        AccountMoveLine.period_id.in_(search_period_ids),
                                        AccountMoveLine.journal_id.in_(vat_journal_ids),
                                        ).order_by(AccountMoveLine.date).all()
                                    )
    else:
        deferred_move_lines=session.query(AccountMoveLine).filter(
                                                AccountMoveLine.company_id==company_id,
                                                AccountMoveLine.account.has(code=deferred_debit_account_code),
                                                AccountMoveLine.period_id.in_(search_period_ids),
                                                AccountMoveLine.journal_id.in_(vat_journal_ids),
                                                ).order_by(AccountMoveLine.date).all()
        deferred_move_lines.extend(session.query(AccountMoveLine).filter(
                                        AccountMoveLine.company_id==company_id,
                                        AccountMoveLine.account.has(code=deferred_credit_account_code),
                                        AccountMoveLine.period_id.in_(search_period_ids),
                                        AccountMoveLine.journal_id.in_(vat_journal_ids),
                                        ).order_by(AccountMoveLine.date).all()
                                    )
                                
    filtered_move_lines=[]
    #filter move_lines according to reconcile_id and that belongs to validated moves
    for line in deferred_move_lines:
        #print "line name=%s date=%s debit=%s credit=%s tax_amount=%s" % (line.name,line.date,line.debit,line.credit,line.tax_amount)
        
        has_been_payed=line.reconcile or line.reconcile_partial
        has_been_payed_in_periods=False
        reconcileAmount=None
        totallyPayed=False
        if has_been_payed:
            reconcileAmount = Decimal(0)
            reconcileLines = []
            if line.reconcile:
                reconcileLines.extend(line.reconcile.lines)
            if line.reconcile_partial:
                reconcileLines.extend(line.reconcile_partial.partial_lines)
            for rec_line in reconcileLines:
                if rec_line.id != line.id:
                    lineAmount = rec_line.credit > 0 and rec_line.credit or rec_line.debit
                    reconcileAmount += lineAmount
                    payment_period = AccountPeriod.getNormalPeriods(AccountPeriod,session,rec_line.date,company_id)[0]
                    #payment_period_id=period_obj.find(cr,uid,rec_line.date,{})[0]
                    has_been_payed_in_periods = (payment_period_ids.count(payment_period.id)>0)
                    line.payment_date = rec_line.date
            totallyPayed = (reconcileAmount==line.tax_amount)
        if get_payments and has_been_payed_in_periods:
            line.deferred_amount = reconcileAmount
            line.reconcile_percentage = line.deferred_amount / line.tax_amount
            filtered_move_lines.append(line)
        elif not get_payments and not has_been_payed_in_periods:
            line.deferred_amount = line.tax_amount
            filtered_move_lines.append(line)
        elif not get_payments and has_been_payed_in_periods and not totallyPayed:
            line.deferred_amount = line.tax_amount - reconcileAmount
            line.reconcile_percentage = line.deferred_amount / line.tax_amount
            filtered_move_lines.append(line)
    
    #build report lines
    report_lines=[]
    for line in filtered_move_lines:
        #compute taxable_amount
        taxable_amount=Decimal('0.00')
        base_code_id=False
        tax=False
        if line.journal.type=='sale_refund' or line.journal.type=='purchase_refund':
            tax=session.query(AccountTax).filter(AccountTax.ref_tax_code_id==line.tax_code_id,AccountTax.company_id==company_id).first()
            base_code_id=tax.ref_base_code_id
        else:
            tax=session.query(AccountTax).filter(AccountTax.tax_code_id==line.tax_code_id,AccountTax.company_id==company_id).first()
            base_code_id=tax.base_code_id
                    
        if base_code_id:
            for m_l in line.move.move_lines:
                if m_l.tax_code_id==base_code_id:
                    taxable_amount+=m_l.tax_amount
        
        #taxable_amount *= line.reconcile_percentage
        taxable_amount = taxable_amount.quantize(Decimal('.01'))
        
        report_line={}
        if get_payments:
            report_line['payment_date']=line.payment_date.strftime("%d-%m-%Y")
        report_line['vat_register']=line.journal.sequence.name
        report_line['protocol_number']=line.move.name
        report_line['date_registration']=line.date.strftime("%d-%m-%Y")
        if line.partner:
            report_line['partner']=line.partner.name
        else:
            report_line['partner']='N.D.'
        report_line['tax_name']=line.name
        report_line['tax_code_id']=line.tax_code_id
        report_line['account_code']=line.account.code
        report_line['taxable_amount']=taxable_amount
        report_line['tax_amount']=line.deferred_amount
        report_lines.append(report_line)
    
    return report_lines
    

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
