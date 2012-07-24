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
import string
import csv
import sys
import os
import getopt

## local libs
## append local lib path
#LIBRARY_PATH = os.path.join(
    #os.path.dirname(os.path.abspath(sys.argv[0])),
    #os.path.pardir, os.path.pardir, 'lib')
#sys.path.append(LIBRARY_PATH)

from config import Config
import Computer


def _printLiquidationSummaryFinalRows(results,documentFileWrapper):
    #append due or credit vat in the period
    vatInThePeriodResults=results['vat_in_the_period']
    documentFileWrapper.appendTexLine("\\multicolumn{2}{|l|}{IVA a debito o credito per il periodo} & "+str(vatInThePeriodResults.get('debit',''))+" & "+str(vatInThePeriodResults.get('credit',''))+" \\\\ \\hline")
    #append debit or credit vat from previous period
    previousPeriodResults=results['previous_period_results']
    documentFileWrapper.appendTexLine("\\multicolumn{2}{|p{13cm}|}{Debito (non superiore a 25,82 Euro) o credito da periodo precedente + acconti IVA} & "+str(previousPeriodResults.get('debit',''))+" & "+str(previousPeriodResults.get('credit',''))+" \\\\ \\hline")
    #append due or credit vat for the period line
    dueOrCreditVatResults=results['due_or_credit_vat']
    documentFileWrapper.appendTexLine("\\multicolumn{2}{|l|}{IVA DOVUTA O A CREDITO PER IL PERIODO} & "+str(dueOrCreditVatResults.get('debit',''))+" & "+str(dueOrCreditVatResults.get('credit',''))+" \\\\ \\hline")
    #append interests lines if present
    interestsResults=results.get('interests',False)
    if interestsResults:
        documentFileWrapper.appendTexLine("\\multicolumn{2}{|l|}{Interessi (1\%)} & "+str(interestsResults.get('debit',''))+" &  \\\\ \\hline")
        dueOrCreditVatResultsWithInterests=results['due_or_credit_vat_with_interest']
        documentFileWrapper.appendTexLine("\\multicolumn{2}{|l|}{IVA DOVUTA PER IL PERIODO CON INTERESSI} & "+str(dueOrCreditVatResultsWithInterests.get('debit',''))+" & \\\\ \\hline")


'''
main method
'''
def main(dirname):
    config = Config()
    config.parse()
    
    dbName=config.db_options.get('database',False)
    user=config.db_options.get('username',False)
    pwd=config.db_options.get('password',False)
    host=config.db_options.get('host',False)
    port=int(config.db_options.get('port',False))
    
    companyName=config.report_options.get('company',False)
    reportType=int(config.report_options.get('report_type',False))
    fiscalyearName=config.report_options.get('fiscalyear',False)
    periodName=config.report_options.get('period',False)
    sequences=config.report_options.get('sequences',False).split(',')
    onlyValidatedMoves=True
    if str(config.report_options.get('onlyValidatedMoves',True))=='False':
        onlyValidatedMoves=False
    
    immediateVatCreditAccountCode=config.accounts.get('immediate_credit_vat_account_code',False)
    immediateVatDebitAccountCode=config.accounts.get('immediate_debit_vat_account_code',False)
    deferredVatCreditAccountCode=config.accounts.get('deferred_credit_vat_account_code',False)
    deferredVatDebitAccountCode=config.accounts.get('deferred_debit_vat_account_code',False)
    treasuryVatAccountCode=config.accounts.get('treasury_vat_account_code',False)
    
    fiscalyear=False
    periodIds=[]
    if periodName and reportType in [2,3,4,5,6]:
        p=dbSession.query(AccountPeriod).filter(AccountPeriod.name==periodName,AccountPeriod.company_id==company.id).first()
        if p:
            periodIds.append(p.id)
        else:
            raise RuntimeError('period %s does not exist for company %s' % (periodName,company.name))
    else:
        fiscalyear=dbSession.query(AccountFiscalyear).filter(AccountFiscalyear.name==fiscalyearName,AccountFiscalyear.company_id==company.id).first()
        if fiscalyear:
            for p in fiscalyear.periods:
                periodIds.append(p.id)
        else:
            raise RuntimeError('fiscalyear %s does not exist for company %s' % (fiscalyearName,company.name))
    
    headerFileWrapper=TexFileWrapper()
    documentFileWrapper=TexFileWrapper()
    pdfFileName=False
    try:
        #vat registers
        if reportType==1:
            lines=Computer.getVatRegisterLines(dbSession,periodIds,company.id,[sequences[0]],onlyValidatedMoves,immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            
            #build tex header part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,51,640,0,0,\
                headRightTex=fiscalyear.name+"/\\thepage\\\\\\large\\textbf{Registro IVA "+sequences[0]+"\\\\}",\
                headLeftTex="\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id),\
                ))
            
            #build tex document part
            documentFileWrapper.appendTexLine("Anno: "+fiscalyearName)
            documentFileWrapper.appendTexLine('''\\scriptsize''')
            rows=[]
            for line in lines:                
                rows.append((\
                    line['date_registration'],\
                    line['protocol_number'],\
                    line['document_date'],\
                    line['reference'],\
                    line['partner_name'],\
                    line['tax_name'],\
                    line['taxable_amount'],\
                    line['tax_amount']\
                ))
            documentFileWrapper.appendTex(TexCodeCreator.getLongTableTex(rows,\
                    columnsDef="|p{1.4cm}|p{1.4cm}|p{1.4cm}|p{2cm}|p{3.7cm}|p{3.5cm}|r|r|",\
                    columnsHeaders=("Data registrazione","Numero protocollo","Data documento","Numero documento","Controparte","Tipo imposta","Imponibile","Imposta"),\
                    horizontalLines=True)\
                )\
                
            pdfFileName="RegistroIVA"+string.replace(sequences[0]," ","")+company.name+string.replace(fiscalyearName," ","")
            
        #vat summary
        elif reportType==2:
            result=Computer.getVatSummaryResults(dbSession,False,periodIds,company.id,sequences,onlyValidatedMoves,immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            
            #build tex document part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,0,640,0,0))
            documentFileWrapper.appendTexLine("\\raggedleft\\large\\textbf{Riepilogo IVA "+sequences[0]+"\\\\}")
            documentFileWrapper.appendTexLine("\\raggedright\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id)+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Periodo: "+periodName)
            documentFileWrapper.appendTexLine("\\footnotesize")
            TexCodeCreator.createVatSummaryDocumentTexCode(documentFileWrapper,result)
            
            pdfFileName="RiepilogoIVA"+string.replace(sequences[0]," ","")+company.name+string.replace(periodName," ","")
            
        #vat detail
        elif reportType==3:
            vatRegisterLines=Computer.getVatRegisterLines(dbSession,periodIds,company.id,sequences,onlyValidatedMoves,immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            summaryResult=Computer.getVatSummaryResults(dbSession,False,periodIds,company.id,sequences,onlyValidatedMoves,immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            
            #build tex document part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,0,640,0,0))
            
            documentFileWrapper.appendTexLine("\\raggedleft\\large\\textbf{Dettaglio movimenti IVA "+sequences[0]+"\\\\}")
            documentFileWrapper.appendTexLine("\\raggedright\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id)+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Periodo: "+periodName+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("\\footnotesize\nLista movimenti")
            documentFileWrapper.appendTexLine('''\\scriptsize''')
            rows=[]
            for line in vatRegisterLines:
                rows.append((\
                    line['date_registration'],\
                    line['protocol_number'],\
                    line['document_date'],\
                    line['reference'],\
                    line['partner_name'],\
                    line['tax_name'],\
                    line['taxable_amount'],\
                    line['tax_amount']\
                ))
            documentFileWrapper.appendTex(TexCodeCreator.getLongTableTex(rows,\
                    columnsDef="|p{1.4cm}|p{1.4cm}|p{1.4cm}|p{2.2cm}|p{3.7cm}|p{3.5cm}|r|r|",\
                    columnsHeaders=("Data registrazione","Numero protocollo","Data documento","Numero documento","Controparte","Tipo imposta","Imponibile","Imposta"),\
                    horizontalLines=True)\
                )\
            
            documentFileWrapper.appendTexLine('''\\newpage''')
            documentFileWrapper.appendTexLine("\\footnotesize\nRiepilogo")
            TexCodeCreator.createVatSummaryDocumentTexCode(documentFileWrapper,summaryResult)
            
            pdfFileName="DettaglioIVA"+string.replace(sequences[0]," ","")+company.name+string.replace(periodName," ","")
            
        #deferred vat detail
        elif reportType==4:
            searchPeriodIds=AccountPeriod.getPreviousPeriodIdsUntilXyears(AccountPeriod,dbSession,periodIds[0],2,company.id)
            searchPeriodIds.append(periodIds[0])
            notPaymentLines=Computer.getDeferredVatDetailLines(dbSession, company.id, False, searchPeriodIds, searchPeriodIds, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            paymentLines=Computer.getDeferredVatDetailLines(dbSession, company.id, True, [periodIds[0]], searchPeriodIds, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            
            #build tex document part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,0,640,0,0))
            documentFileWrapper.appendTexLine("\\raggedleft\\large\\textbf{Dettaglio IVA ad esigibilita\' differita\\\\}")
            documentFileWrapper.appendTexLine("\\raggedright\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id)+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Periodo: "+periodName+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Incassati e pagati nel periodo")
            rows=[]
            for line in paymentLines:
                proto=line['protocol_number'].split("/")
                proto=proto[len(proto)-1]
                rows.append((\
                    line['payment_date'],\
                    line['vat_register'],\
                    proto,\
                    line['date_registration'],\
                    line['partner'],\
                    line['tax_name'],\
                    line['taxable_amount'],\
                    line['tax_amount']\
                ))
            documentFileWrapper.appendTex(TexCodeCreator.getLongTableTex(rows,\
                    columnsDef="|p{1.7cm}|p{2cm}|p{1.3cm}|p{1.7cm}|p{2.8cm}|p{3.5cm}|r|r|",\
                    columnsHeaders=("Data incasso o pagamento","Registro IVA","Numero protocollo","Data registrazione","Controparte","Tipo imposta","Imponibile","Imposta"),\
                    horizontalLines=True)\
                )\
            
            documentFileWrapper.appendTexLine("\\")
            documentFileWrapper.appendTexLine("Da incassare o pagare")
            rows=[]
            for line in notPaymentLines:
                proto=line['protocol_number'].split("/")
                proto=proto[len(proto)-1]
                rows.append((\
                    line['vat_register'],\
                    proto,\
                    line['date_registration'],\
                    line['partner'],\
                    line['tax_name'],\
                    line['taxable_amount'],\
                    line['tax_amount']\
                ))
            documentFileWrapper.appendTex(TexCodeCreator.getLongTableTex(rows,\
                    columnsDef="|p{2cm}|p{1.5cm}|p{1.7cm}|p{3.8cm}|p{4.4cm}|r|r|",\
                    columnsHeaders=("Registro IVA","Numero protocollo","Data registrazione","Controparte","Tipo imposta","Imponibile","Imposta"),\
                    horizontalLines=True)\
                )\
            
            pdfFileName="DettaglioIVAEsigibDifferita"+company.name+string.replace(periodName," ","")
            
        #deferred vat summary
        elif reportType==5:
            sequenceNames=IrSequence.getVatSequencesNames(IrSequence,dbSession,company.id)
            searchPeriodIds=AccountPeriod.getPreviousPeriodIdsUntilXyears(AccountPeriod,dbSession,periodIds[0],2,company.id)
            searchPeriodIds.append(periodIds[0])
            
            results=Computer.getDeferredVatSummaryLines(dbSession, company.id, sequenceNames, [periodIds[0]], searchPeriodIds, onlyValidatedMoves, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            
            #build tex document part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,0,640,0,0))
            documentFileWrapper.appendTexLine("\\raggedleft\\large\\textbf{Riepilogo IVA ad esigibilita\' differita\\\\}")
            documentFileWrapper.appendTexLine("\\raggedright\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id)+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Periodo: "+periodName+"\\\\[15pt]")
            
            #print sequences table
            documentFileWrapper.appendTexLine("Riepilogo")
            documentFileWrapper.appendTexLine("\\begin{longtable}[l]{|p{10.7cm}|p{3.6cm}|r|r|}")
            documentFileWrapper.appendTexLine("\\hline")
            documentFileWrapper.appendTexLine("Registro IVA & & Imponibile & Imposta \\\\ \\hline")
            for sequence in results['sequences']:
                values=sequence[sequence.keys()[0]]
                documentFileWrapper.appendTexLine("\\multicolumn{4}{|l|}{"+sequence.keys()[0]+"} \\\\ \\hline")                
                
                for tax in values['taxes']:
                    documentFileWrapper.appendTexLine("\\multirow{2}{*}{"+TexCodeCreator.getPrintableTexString(tax['tax_name'])+"}")
                    row=('Incassata o pagata',tax['payments_taxable_amount'],tax['payments_tax_amount'])
                    documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{2-4}")
                    row=('Da incassare o pagare',tax['not_payments_taxable_amount'],tax['not_payments_tax_amount'])
                    documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{1-4}")
                    
                documentFileWrapper.appendTexLine("\\multirow{2}{*}{Totale IVA incassata o pagata}")
                row=('A debito',values['paid_received_totals']['debit_taxable_amount'],values['paid_received_totals']['debit_tax_amount'])
                documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{2-4}")
                row=('A credito',values['paid_received_totals']['credit_taxable_amount'],values['paid_received_totals']['credit_tax_amount'])
                documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{1-4}")
                
                documentFileWrapper.appendTexLine("\\multirow{2}{*}{Totale IVA da incassare o pagare}")
                row=('A debito',values['pay_receive_totals']['debit_taxable_amount'],values['pay_receive_totals']['debit_tax_amount'])
                documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{2-4}")
                row=('A credito',values['pay_receive_totals']['credit_taxable_amount'],values['pay_receive_totals']['credit_tax_amount'])
                documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\hline")
            documentFileWrapper.appendTexLine("\\end{longtable}")
            
            #print synthesis table
            documentFileWrapper.appendTexLine("\\vspace{10 mm}")
            documentFileWrapper.appendTexLine("Sintesi")
            documentFileWrapper.appendTexLine("\\begin{longtable}[l]{|p{5cm}|p{3.5cm}|r|r|}")
            documentFileWrapper.appendTexLine("\\hline")
            
            documentFileWrapper.appendTexLine("\\multirow{2}{*}{Totale IVA incassata o pagata}")
            row=('A debito',results['paid_received_totals']['debit_taxable_amount'],results['paid_received_totals']['debit_tax_amount'])
            documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{2-4}")
            row=('A credito',results['paid_received_totals']['credit_taxable_amount'],results['paid_received_totals']['credit_tax_amount'])
            documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\hline")
            
            documentFileWrapper.appendTexLine("\\multirow{2}{*}{Totale IVA da incassare o pagare}")
            row=('A debito',results['pay_receive_totals']['debit_taxable_amount'],results['pay_receive_totals']['debit_tax_amount'])
            documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\cline{2-4}")
            row=('A credito',results['pay_receive_totals']['credit_taxable_amount'],results['pay_receive_totals']['credit_tax_amount'])
            documentFileWrapper.appendTexLine("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False)+" \\hline")
            
            documentFileWrapper.appendTexLine("\\end{longtable}")
            
            pdfFileName="RiepilogoIVAEsigibDifferita"+company.name+string.replace(periodName," ","")
            
        #vat liquidation
        elif reportType==6:
            results=Computer.getVatLiquidationSummaryLines(dbSession, periodIds[0], company.id, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode)
            
            #build tex document part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,0,640,0,0))
            documentFileWrapper.appendTexLine("\\raggedleft\\large\\textbf{Prospetto liquidazione IVA\\\\}")
            documentFileWrapper.appendTexLine("\\raggedright\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id)+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Periodo: "+periodName+"\\\\")
            
            documentFileWrapper.appendTexLine("\\footnotesize")
            documentFileWrapper.appendTexLine("\\begin{longtable}[l]{|p{6cm}|p{7cm}|r|r|}")
            documentFileWrapper.appendTexLine("\\hline")
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|c|}{} & IVA a debito & IVA a credito \\\\ \\hline")
            #append immediate vat lines
            documentFileWrapper.appendTexLine("\\multirow{"+str(len(results['immediate_vat_amounts']))+"}{*}{IVA ad esigibilita\' immediata}")
            for i in range(0,len(results['immediate_vat_amounts'])):
                immediate_amounts=results['immediate_vat_amounts'][i]
                row=(immediate_amounts['sequence_name'],immediate_amounts['debit'],immediate_amounts['credit'])
                documentFileWrapper.appendTex("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False))
                if i<len(results['immediate_vat_amounts'])-1:
                    documentFileWrapper.appendTexLine(" \\cline{2-4}")
                else:
                    documentFileWrapper.appendTexLine(" \\hline")
            #append deferred vat lines
            deferredVatResults=results['deferred_vat_amounts']
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|l|}{IVA esigibile da esigibilita\' differita} & "+str(deferredVatResults.get('debit',''))+" & "+str(deferredVatResults.get('credit',''))+" \\\\ \\hline")
            #append total line
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|l|}{Totale} & "+str(results['vat_totals_amounts']['debit'])+" & "+str(results['vat_totals_amounts']['credit'])+" \\\\ \\hline")
            #append empty line
            documentFileWrapper.appendTexLine("\\multicolumn{4}{|l|}{} \\\\ \\hline")
            
            _printLiquidationSummaryFinalRows(results,documentFileWrapper)
                        
            documentFileWrapper.appendTexLine("\\end{longtable}")
            
            pdfFileName="ProspettoLiquidazioneIVA"+company.name+string.replace(periodName," ","")
            
        #exercise control summary
        elif reportType==7:
            sequenceNames=IrSequence.getVatSequencesNames(IrSequence,dbSession,company.id)

            vatSummaryResults=Computer.getVatSummaryResults(dbSession, False, periodIds, company.id, sequenceNames, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            controlSummaryResults=Computer.getControlSummaryVatLines(dbSession, vatSummaryResults, sequenceNames, company.id, fiscalyear.id, onlyValidatedMoves, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode)
            
            #build tex document part
            headerFileWrapper.appendTex(TexCodeCreator.getFancyStyleTex(0,0,640,0,0))
            documentFileWrapper.appendTexLine("\\raggedleft\\large\\textbf{Prospetto di controllo esercizio\\\\}")
            documentFileWrapper.appendTexLine("\\raggedright\\footnotesize "+ResCompany.getCompanyHeaderTex(ResCompany,dbSession,company.id)+"\\\\[15pt]")
            documentFileWrapper.appendTexLine("Anno: "+fiscalyearName+"\\\\[25pt]")
            
            #append vat summary table
            documentFileWrapper.appendTexLine("Riepilogo IVA")
            documentFileWrapper.appendTexLine("\\footnotesize")
            TexCodeCreator.createVatSummaryDocumentTexCode(documentFileWrapper,vatSummaryResults)
            
            #append summary with vat now exigible
            documentFileWrapper.appendTexLine("\\newpage")
            documentFileWrapper.appendTexLine("\\footnotesize Riepilogo con IVA diventata esigibile")
            documentFileWrapper.appendTexLine("\\footnotesize")
            documentFileWrapper.appendTexLine("\\begin{longtable}[l]{|p{5cm}|p{5cm}|r|r|r|r|}")
            documentFileWrapper.appendTexLine("\\cline{3-6}")
            documentFileWrapper.appendTexLine("\\multicolumn{2}{c}{} & \\multicolumn{2}{|c|}{Iva a debito} &  \\multicolumn{2}{|c|}{Iva a credito} \\\\ \\hline")
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|c|}{} & Imponibile & Imposta & Imponibile & Imposta \\\\ \\hline")
            #append immediate vat totals line
            immediateVatTotals=vatSummaryResults['immediate_total']
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|p{10cm}|}{IVA AD ESIG. IMMEDIATA REGISTRATA NELL'ESERCIZIO} &  "+\
                                            str(immediateVatTotals['debit_taxable_amount'])+" &"+\
                                            str(immediateVatTotals['debit_tax_amount'])+" &"+\
                                            str(immediateVatTotals['credit_taxable_amount'])+" &"+\
                                            str(immediateVatTotals['credit_tax_amount'])+\
                                            "\\\\ \\hline")
            #append deferred vat totals line
            deferredVatTotals=vatSummaryResults['deferred_total']
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|p{10cm}|}{IVA AD ESIG. DIFFERITA REGISTRATA NELL'ESERCIZIO} &  "+\
                                            str(deferredVatTotals['debit_taxable_amount'])+" &"+\
                                            str(deferredVatTotals['debit_tax_amount'])+" &"+\
                                            str(deferredVatTotals['credit_taxable_amount'])+" &"+\
                                            str(deferredVatTotals['credit_tax_amount'])+\
                                            "\\\\ \\hline")
            #append empty line
            documentFileWrapper.appendTexLine("\\multicolumn{6}{|p{10cm}|}{} \\\\ \\hline")
            #append deferred vat now exigible lines
            documentFileWrapper.appendTexLine("\\multirow{3}{5cm}{IVA AD ESIG. DIFFERITA \\\\ ESIGIBILE NELL' ESERCIZIO}")
            
            previousExerciseDeferredVatNowExigibleAmounts=controlSummaryResults['previous_exercise_deferred_vat_now_exigible_amounts']
            row=("registrata nell'esercizio precedente",previousExerciseDeferredVatNowExigibleAmounts['debit_taxable'],previousExerciseDeferredVatNowExigibleAmounts['debit_tax'],previousExerciseDeferredVatNowExigibleAmounts['credit_taxable'],previousExerciseDeferredVatNowExigibleAmounts['credit_tax'])
            documentFileWrapper.appendTex("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False))
            documentFileWrapper.appendTexLine("\\cline{2-6}")
            
            currentExerciseDeferredVatNowExigibleAmounts=controlSummaryResults['current_exercise_deferred_vat_now_exigible_amounts']
            row=("registrata nell'esercizio corrente",currentExerciseDeferredVatNowExigibleAmounts['debit_taxable'],currentExerciseDeferredVatNowExigibleAmounts['debit_tax'],currentExerciseDeferredVatNowExigibleAmounts['credit_taxable'],currentExerciseDeferredVatNowExigibleAmounts['credit_tax'])
            documentFileWrapper.appendTex("& "+TexCodeCreator.getTableRowTex(row,horizontalSeparator=False))
            documentFileWrapper.appendTexLine("\\cline{2-6}")
            
            deferredVatNowExigibleTotalAmounts=controlSummaryResults['deferred_vat_now_exigible_total_amounts']
            row=("TOTALE",deferredVatNowExigibleTotalAmounts['debit_taxable'],deferredVatNowExigibleTotalAmounts['debit_tax'],deferredVatNowExigibleTotalAmounts['credit_taxable'],deferredVatNowExigibleTotalAmounts['credit_tax'])
            documentFileWrapper.appendTex("& "+TexCodeCreator.getTableRowTex(row))
            documentFileWrapper.appendTexLine("\\hline")
            #append empty line
            documentFileWrapper.appendTexLine("\\multicolumn{6}{|p{10cm}|}{} \\\\ \\hline")
            #append vat exigible in current exercise totals
            vatNowExigibleTotals=controlSummaryResults['vat_now_exigible_total_amounts']
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|p{10cm}|}{TOTALE IVA ESIGIBILE NELL'ESERCIZIO CORRENTE} &  "+\
                                            str(vatNowExigibleTotals['debit_taxable'])+" &"+\
                                            str(vatNowExigibleTotals['debit_tax'])+" &"+\
                                            str(vatNowExigibleTotals['credit_taxable'])+" &"+\
                                            str(vatNowExigibleTotals['credit_tax'])+\
                                            "\\\\ \\hline")
            #append empty line
            documentFileWrapper.appendTexLine("\\multicolumn{6}{|p{11cm}|}{} \\\\ \\hline")
            #append deferred vat to require in next exercise totals
            deferredVatToRequireInNextExerciseTotals=controlSummaryResults['deferred_vat_to_require_in_next_exercise']
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|p{11cm}|}{IVA AD ESIGIBILITA' DIFFERITA DA ESIGERE NELL'ESERCIZIO SUCCESSIVO} &  "+\
                                            str(deferredVatToRequireInNextExerciseTotals['debit_taxable'])+" &"+\
                                            str(deferredVatToRequireInNextExerciseTotals['debit_tax'])+" &"+\
                                            str(deferredVatToRequireInNextExerciseTotals['credit_taxable'])+" &"+\
                                            str(deferredVatToRequireInNextExerciseTotals['credit_tax'])+\
                                            "\\\\ \\hline")
            
            documentFileWrapper.appendTexLine("\\end{longtable}")
            documentFileWrapper.appendTexLine("\\vspace{10 mm}")
            
            dueOrCreditVat=vatNowExigibleTotals['debit_tax']-vatNowExigibleTotals['credit_tax']            
            maxPeriodId=-1
            for id in periodIds:
                if id > maxPeriodId:
                    maxPeriodId=id
            
            finalResults=Computer.getLiquidationSummaryFinalLines(dbSession, dueOrCreditVat, company.id, maxPeriodId, treasuryVatAccountCode)
            #append final results
            documentFileWrapper.appendTexLine("\\footnotesize Liquidazione IVA")
            documentFileWrapper.appendTexLine("\\footnotesize")
            documentFileWrapper.appendTexLine("\\begin{longtable}[l]{|p{2.5cm}||p{2.5cm}|r|r|}")
            documentFileWrapper.appendTexLine("\\hline")
            documentFileWrapper.appendTexLine("\\multicolumn{2}{|c|}{} & Iva a debito &  Iva a credito \\\\ \\hline")
            _printLiquidationSummaryFinalRows(finalResults,documentFileWrapper)
            
            documentFileWrapper.appendTexLine("\\end{longtable}")
            
            
            pdfFileName="ProspettoControlloEsercizio"+company.name+string.replace(fiscalyearName," ","")
            
    except:
        raise

    #create tex files
    basepath = os.path.join(dirname, os.path.pardir, os.path.pardir)
    texDirPath=os.path.join(basepath, "templates")
    Tools.writeTex(headerFileWrapper, os.path.join(texDirPath,"header.tex"))
    Tools.writeTex(documentFileWrapper, os.path.join(texDirPath,"document.tex"))
    
    #create pdf file

    templateTexDirPath=os.path.join(texDirPath,"template.tex")
    pdfdirPath=os.path.join(basepath,"pdf")
    pdfFilePath=os.path.join(pdfdirPath,string.replace(pdfFileName,"/","")+".pdf")
   
    if not os.path.exists(pdfdirPath):
        os.makedirs(pdfdirPath)
    if pdfFileName:
        os.system("texi2pdf -o "+pdfFilePath+" -I "+texDirPath+" -c --quiet "+templateTexDirPath)
    return 0


if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
