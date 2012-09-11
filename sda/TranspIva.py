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

SRE_PATH = os.path.join(BASEPATH,"sre")

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
    #lettura degli oggetti stark di interesse
    companyPathPkl = os.path.join(picklesPath,comNam)
    vatStarK = Stark.load(os.path.join(companyPathPkl,"VAT.pickle"))
    vatDf = vatStarK.DF
    periodStarK = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    periodDf = periodStarK.DF
    companyStarK = Stark.load(os.path.join(companyPathPkl,"COMP.pickle"))
    companyDf = companyStarK.DF
    companyString = companyDf['NAME'][0]+" \linebreak "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+"\linebreak P.IVA "+companyDf['VAT'][0]
    #in  base al tipo di report scelto dall'utente, il programma lancia la funzione corrispondente
    try:
        #vat registers
        if reportType==1:
            vatRegister = SDAIva.getVatRegister(vatDf, comNam, onlyValML, fiscalyearName=fiscalyearName, sequenceName=sequenceName)
            bagVatRegister = Bag(DF=vatRegister,TIP='tab',LM=CreateLMIva.lm_registri_iva)
            setattr(bagVatRegister,"SEQUENCE",sequenceName)
            setattr(bagVatRegister,"YEAR",fiscalyearName)
            setattr(bagVatRegister,"COMPANY_STRING",companyString)
            OUT_PATH = os.path.join(SRE_PATH, 'registro_iva')
            bagVatRegister.save(os.path.join(OUT_PATH, 'vat_register.pickle'))
        #vat summary
        elif reportType==2:
            vatSummary=SDAIva.getVatSummary(vatDf, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            bagVatSummary = Bag(DF=vatSummary,TIP='tab',LM=CreateLMIva.lm_riepiloghi_iva,TITLE='Riepilogo IVA '+sequenceName)
            setattr(bagVatSummary,"PERIOD",periodName)
            setattr(bagVatSummary,"COMPANY_STRING",companyString)
            OUT_PATH = os.path.join(SRE_PATH, 'riepilogo_iva')
            bagVatSummary.save(os.path.join(OUT_PATH, 'vat_summary.pickle'))
        #vat detail
        elif reportType==3:
            vatRegister = SDAIva.getVatRegister(vatDf, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            bagVatRegister = Bag(DF=vatRegister,TIP='tab',LM=CreateLMIva.lm_registri_iva,TITLE='Dettaglio IVA '+sequenceName)
            setattr(bagVatRegister,"PERIOD",periodName)
            setattr(bagVatRegister,"COMPANY_STRING",companyString)
            vatSummary=SDAIva.getVatSummary(vatDf, comNam, onlyValML, periodName=periodName, sequenceName=sequenceName)
            bagVatSummary = Bag(DF=vatSummary,TIP='tab',LM=CreateLMIva.lm_riepiloghi_iva,TITLE='Riepilogo')
            OUT_PATH = os.path.join(SRE_PATH, 'dettaglio_iva')
            bagVatRegister.save(os.path.join(OUT_PATH, 'vat_register.pickle'))
            bagVatSummary.save(os.path.join(OUT_PATH, 'vat_summary.pickle'))
        #deferred vat detail
        elif reportType==4:            
            payments = SDAIva.getDeferredVatDetailPayments(vatDf, comNam, onlyValML, paymentsPeriodName=periodName)
            notPayed = SDAIva.getDeferredVatDetailNotPayed(vatDf, comNam, onlyValML, periodDf, paymentsPeriodName=periodName)
            bagPayments = Bag(DF=payments,TIP='tab',LM=CreateLMIva.lm_pagamenti_iva_differita,TITLE="Dettaglio IVA \nad esigibilita' differita")
            setattr(bagPayments,"PERIOD",periodName)
            setattr(bagPayments,"COMPANY_STRING",companyString)
            bagNotPayed = Bag(DF=notPayed,TIP='tab',LM=CreateLMIva.lm_da_pagare_iva_differita)
            OUT_PATH = os.path.join(SRE_PATH, 'dettaglio_iva_differita')
            bagPayments.save(os.path.join(OUT_PATH, 'payments.pickle'))
            bagNotPayed.save(os.path.join(OUT_PATH, 'not_payed.pickle'))
        #deferred vat summary
        elif reportType==5:
            deferredVatSummaryDf = SDAIva.getDeferredVatSummary(vatDf, comNam, onlyValML, 
                                                            periodDf, paymentsPeriodName=periodName)
            bagSummary= Bag(DF=deferredVatSummaryDf['dfSummary'],TIP='tab',LM=CreateLMIva.lm_riepilogo_differita,TITLE="Riepilogo")
            setattr(bagSummary,"PERIOD",periodName)
            setattr(bagSummary,"COMPANY_STRING",companyString)
            bagSynthesis= Bag(DF=deferredVatSummaryDf['dfSynthesis'],TIP='tab',LM=CreateLMIva.lm_riepilogo_differita,TITLE="Sintesi")
            OUT_PATH = os.path.join(SRE_PATH, 'riepilogo_iva_differita')
            bagSummary.save(os.path.join(OUT_PATH, 'deferred_vat_summary.pickle'))
            bagSynthesis.save(os.path.join(OUT_PATH, 'deferred_vat_synthesis.pickle'))
        #vat liquidation
        elif reportType==6:
            liquidationSummary = SDAIva.getVatLiquidationSummary(vatDf, periodDf,
                                                                comNam, onlyValML, treasuryVatAccountCode, periodName=periodName)
            bagLiquidationSummary = Bag(DF=liquidationSummary,TIP='tab',LM=CreateLMIva.lm_liquidazione_iva,TITLE='Prospetto liquidazione Iva')
            setattr(bagLiquidationSummary,"PERIOD",periodName)
            setattr(bagLiquidationSummary,"COMPANY_STRING",companyString)
            OUT_PATH = os.path.join(SRE_PATH, 'liquidazione_iva')
            bagLiquidationSummary.save(os.path.join(OUT_PATH, 'liquidation_summary.pickle'))
        #exercise control summary
        elif reportType==7:
            vatSummary = SDAIva.getVatSummary(vatDf, comNam, onlyValML, fiscalyearName=fiscalyearName)
            vatControlSummaryDf = SDAIva.getVatControlSummary(fiscalyearName, vatSummary, vatDf, 
                                                            periodDf, comNam, onlyValML, treasuryVatAccountCode)
            OUT_PATH = os.path.join(SRE_PATH, 'controllo_esercizio')
            bagVatSummary = Bag(DF=vatSummary,TIP='tab',LM=CreateLMIva.lm_riepiloghi_iva,TITLE='Riepilogo IVA')
            setattr(bagVatSummary,"YEAR",fiscalyearName)
            setattr(bagVatSummary,"COMPANY_STRING",companyString)
            bagVatSummary.save(os.path.join(OUT_PATH, 'vat_summary.pickle'))
            bagSummary2 = Bag(DF=vatControlSummaryDf['summary'],TIP='tab',LM=CreateLMIva.lm_controllo_esercizio,TITLE='Riepilogo con IVA diventata esigibile')
            bagSummary2.save(os.path.join(OUT_PATH, 'vat_summary_2.pickle'))
            bagLiquidationSummary = Bag(DF=vatControlSummaryDf['liquidationSummary'],TIP='tab',LM=CreateLMIva.lm_controllo_esercizio,TITLE='Liquidazione IVA')
            bagLiquidationSummary.save(os.path.join(OUT_PATH, 'liquidation_summary.pickle'))
    except:
        raise

    return 0


if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))