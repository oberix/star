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

lm_flussi = {
        'descrizione': [0, '3l', '@v10'],
        1: [1, 'r', 'gen'],
        2: [2, 'r', 'feb'],
        3: [3, 'r', 'mar'],
        4: [4, 'r', 'apr'],
        5: [5, 'r', 'mag'],
        6: [6, 'r', 'giu'],
        7: [7, 'r', 'lug'],
        8: [8, 'r', 'ago'],
        9: [9, 'r', 'set'],
        10: [10, 'r', 'ott'],
        11: [11, 'r', 'nov'],
        12: [12, 'r', 'dic'],
        'TOTAL': [13, 'r', 'TOTALE'],
        }
        
lm_journals = {
        'NAM_JRN': [0, '3l', '@v10'],
        1: [1, 'r', 'gen'],
        2: [2, 'r', 'feb'],
        3: [3, 'r', 'mar'],
        4: [4, 'r', 'apr'],
        5: [5, 'r', 'mag'],
        6: [6, 'r', 'giu'],
        7: [7, 'r', 'lug'],
        8: [8, 'r', 'ago'],
        9: [9, 'r', 'set'],
        10: [10, 'r', 'ott'],
        11: [11, 'r', 'nov'],
        12: [12, 'r', 'dic'],
        }


import sys
import os
import getopt
import pandas
import FlussiCassaLib
import ScadenziarioLib
from datetime import date
from datetime import datetime

import sda
from share import Config
from share import Stark
from share import Bag

SRE_PATH = os.path.join(BASEPATH,"sre")

def main(dirname):
    #legge il file config    
    configFilePath = os.path.join(BASEPATH,"config","flussi_cassa.cfg")
    config = Config(configFilePath)
    config.parse()
    #assegna ai parametri di interesse il valore letto in config
    companyName = config.options.get('company',False)
    picklesPath = config.options.get('pickles_path',False)
    fiscalyearName=config.options.get('fiscalyear',False)
    defaultIncomingsFlowLineCode = config.options.get('default_incomings_flow_line',False)
    defaultExpensesFlowLineCode = config.options.get('default_expenses_flow_line',False)
    totalIncomingsFlowLineCode = config.options.get('total_incomings_flow_line',False)
    totalExpensesFlowLineCode = config.options.get('total_expenses_flow_line',False)
    referenceDate = config.options.get('reference_date',False)
    linesCsvFilePath = config.options.get('lines_csv_file_path',False)
    matchingsCsvFilePath = config.options.get('matchings_csv_file_path',False)
    fixedCostsCsvFilePath = config.options.get('fixed_costs_csv_file_path',False)
    #verifica del parametro reference_date
    if len(referenceDate) < 8:
        referenceDate = date.today()
    else:
        referenceDate = datetime.strptime(referenceDate,"%d-%m-%Y")
        referenceDate = referenceDate.date()
    #verifica che la stringa associata al parametro only_validated_moves inserita in config
    #sia effettivamente un valore boleano 
    onlyValidatedMoves = True
    if str(config.options.get('only_validated_moves',True))=='False':
        onlyValidatedMoves = False
    #lettura degli oggetti stark di interesse
    companyPathPkl = os.path.join(picklesPath,companyName)
    accountStark = Stark.load(os.path.join(companyPathPkl,"ACC.pickle"))
    periodStark = Stark.load(os.path.join(companyPathPkl,"PERIOD.pickle"))
    moveLineStark = Stark.load(os.path.join(companyPathPkl,"MVL.pickle"))
    companyStarK = Stark.load(os.path.join(companyPathPkl,"COMP.pickle"))
    invoiceStark = Stark.load(os.path.join(companyPathPkl,"INV.pickle"))
    voucherStark = Stark.load(os.path.join(companyPathPkl,"VOU.pickle"))
    companyDf = companyStarK.df
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    #lettura csv
    linesDf = pandas.read_csv(linesCsvFilePath, sep=";", header=0)
    matchingsDf = pandas.read_csv(matchingsCsvFilePath, sep=";", header=0)
    fixedCostsDf = pandas.read_csv(fixedCostsCsvFilePath, sep=";", header=0)
    #controllo conti
    FlussiCassaLib.checkAccounts(matchingsDf,accountStark.df)
    #calcolo flussi effettivi
    results = FlussiCassaLib.computeCashFlows(fiscalyearName,moveLineStark.df,accountStark.df,
                    periodStark.df,linesDf,matchingsDf,fixedCostsDf,onlyValidatedMoves,
                    defaultIncomingsFlowLineCode,defaultExpensesFlowLineCode,
                    printWarnings=False)
    companyString = companyDf['NAME'][0]+" - "+companyDf['ADDRESS'][0]+" \linebreak "+companyDf['ZIP'][0]+" "+companyDf['CITY'][0]+" P.IVA "+companyDf['VAT'][0]
    OUT_PATH = os.path.join(SRE_PATH, 'flussi_cassa')
    concatDf = pandas.concat([results['cashFlows'],results['diffEntUsc'],results['saldoAgg']])
    bagFlows = Bag(concatDf, os.path.join(OUT_PATH, 'cash_flows.pickle'), bag_type='tab',meta=lm_flussi)
    setattr(bagFlows,"YEAR",fiscalyearName)
    setattr(bagFlows,"COMPANY_STRING",companyString)
    setattr(bagFlows,"COMPANY",companyName)
    bagFlows.save()
    bagJournals = Bag(results['saldoJournals'], os.path.join(OUT_PATH, 'journals.pickle'), bag_type='tab',meta=lm_journals)
    bagJournals.save()
    #calcolo flussi previsionali
    expiries = ScadenziarioLib.computeExpiries(invoiceStark.df,voucherStark.df,periodStark.df,moveLineStark.df,fiscalyearName)
    forecastedFlowsDf = FlussiCassaLib.computeForecastedFlows(results['cashFlows'],referenceDate,expiries)
    bagForecastedFlows = Bag(forecastedFlowsDf, os.path.join(OUT_PATH, 'forecasted_flows.pickle'), bag_type='tab',meta=lm_flussi)
    bagForecastedFlows.save()
    return 0
    
if __name__ == "__main__":
    abspath=os.path.abspath(sys.argv[0])
    dirname=os.path.dirname(abspath)
    sys.exit(main(dirname))
