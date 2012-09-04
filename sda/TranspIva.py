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

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
                os.path.dirname(__file__),
                os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))

OUT_PATH = os.path.join(BASEPATH,"sre","registro_iva")

from share import Config
from share import Stark
from share import Bag
import SDAIva
import CreateLMIva

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
    #verifica che la stringa associata al parametro only_validated_moves inserita in configù
    #sia effettivamente un valore boleano 
    onlyValML=True
    if str(config.options.get('only_validated_moves',True))=='False':
        onlyValML=False

    #lettura dell'oggetto stark di interesse VAT.pickle    
    companyPathPkl = os.path.join(picklesPath,comNam)
    vatStarK = Stark.load(os.path.join(companyPathPkl,"VAT.pickle"))
    vatDf = vatStarK.DF
    
    pdfFileName=False
    #in  base al tipo di report scelto dall'utente, il porgramma lancia la funzione corrispondente
    try:
        #vat registers
        if reportType==1:
            vatRegister = SDAIva.getVatRegister(vatDf, comNam, onlyValML, fiscalyearName=fiscalyearName, sequenceName=sequenceName)
            bagRIva = Bag(DF=vatRegister,TIP='tab',LM=CreateLMIva.lm_registri_iva,TITLE='Registro IVA '+sequenceName)
            setattr(bagRIva,"YEAR",fiscalyearName)
            bagRIva.save(os.path.join(OUT_PATH, 'vat_register.pickle'))
            #pdfFileName = "RegistroIVA"+string.replace(sequenceName," ","")+comNam+string.replace(fiscalyearName," ","")
        #vat summary
        elif reportType==2:
            vatSummary=SDAIva.getVatSummary(vatDf, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            bagRIva = Bag(DF=vatSummary,TIP='tab',LM=CreateLMIva.lm_riepiloghi_iva,TITLE='Riepilogo IVA '+sequenceName)
            setattr(bagRIva,"PERIOD",periodName)
            bagRIva.save(os.path.join(OUT_PATH, 'vat_summary.pickle'))
            #pdfFileName="RiepilogoIVA"+string.replace(sequenceName," ","")+comNam+string.replace(periodName," ","")
        ##vat detail
        #elif reportType==3:
            #vatRegister = SDAIva.getVatRegister(picklesPath, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            #print vatRegister
            #bagRIva = Bag(DF=vatRegister,TIP='tab',LM=CreateLMIva.lm_registri_iva)
            #vatSummary=SDAIva.getVatSummary(picklesPath, comNam, onlyValML, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, periodName=periodName, sequenceName=sequenceName)
            #print vatSummary
            #pdfFileName="DettaglioIVA"+string.replace(sequenceName," ","")+comNam+string.replace(periodName," ","")
        ##deferred vat detail
        #elif reportType==4:            
            #payments = SDAIva.getDeferredVatDetail(picklesPath, comNam, onlyValML, deferredVatCreditAccountCode, deferredVatDebitAccountCode, searchPayments=True, paymentsPeriodName=periodName)
            #notPayed = SDAIva.getDeferredVatDetail(picklesPath, comNam, onlyValML, deferredVatCreditAccountCode, deferredVatDebitAccountCode, searchPayments=False, paymentsPeriodName=periodName)
            #print payments
            #print notPayed
            #transportPayments = Bag(DF=payments,TIP='tab',LM=CreateLMIva.lm_pagamenti_iva_differita)
            #transportNotPayed = Bag(DF=notPayed,TIP='tab',LM=CreateLMIva.lm_da_pagare_iva_differita)
            #pdfFileName="DettaglioIVAEsigibDifferita"+comNam+string.replace(periodName," ","")
        ##deferred vat summary
        #elif reportType==5:
            #deferredVatSummary = SDAIva.getDeferredVatSummary(picklesPath, comNam, onlyValML, deferredVatCreditAccountCode, deferredVatDebitAccountCode, paymentsPeriodName=periodName)
            #print deferredVatSummary
            #pdfFileName="RiepilogoIVAEsigibDifferita"+comNam+string.replace(periodName," ","")
        ##vat liquidation
        #elif reportType==6:
            #liquidationSummary = SDAIva.getVatLiquidationSummary(picklesPath, comNam, onlyValML, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode, periodName=periodName)
            #print liquidationSummary
            #pdfFileName="ProspettoLiquidazioneIVA"+comNam+string.replace(periodName," ","")
        ##exercise control summary
        #elif reportType==7:
            #vatSummary = SDAIva.getVatSummary(picklesPath, comNam, onlyValML, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, fiscalyearName=fiscalyearName)
            ##print vatSummary
            #vatControlSummary = SDAIva.getVatControlSummary(fiscalyearName, vatSummary, picklesPath, comNam, onlyValML, immediateVatCreditAccountCode, immediateVatDebitAccountCode, deferredVatCreditAccountCode, deferredVatDebitAccountCode, treasuryVatAccountCode)
                        
            #pdfFileName="ProspettoControlloEsercizio"+comNam+string.replace(fiscalyearName," ","")
            
    except:
        raise

    #create tex files
    #basepath = os.path.join(dirname, os.path.pardir, os.path.pardir)
    #texDirPath=os.path.join(basepath, "templates")
    #Tools.writeTex(headerFileWrapper, os.path.join(texDirPath,"header.tex"))
    #Tools.writeTex(documentFileWrapper, os.path.join(texDirPath,"document.tex"))
    
    ##create pdf file

    #templateTexDirPath=os.path.join(texDirPath,"template.tex")
    #pdfdirPath=os.path.join(basepath,"pdf")
    #pdfFilePath=os.path.join(pdfdirPath,string.replace(pdfFileName,"/","")+".pdf")
   
    #if not os.path.exists(pdfdirPath):
        #os.makedirs(pdfdirPath)
    #if pdfFileName:
        #os.system("texi2pdf -o "+pdfFilePath+" -I "+texDirPath+" -c --quiet "+templateTexDirPath)
    return 0


if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
