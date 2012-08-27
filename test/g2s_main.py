import sys
import os
import difflib
import csv

# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
import etl

path_cvs = 'goal2stark.csv'

gv_ml = {
      'accountAccount_code' : 
        {
         'NAME' : 'CODA',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'codice identificativo del conto',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      
      'accountAccount_name' : 
        {
         'NAME' : 'NOMA',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'nome descrittivo del conto',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      
      'accountMoveLine_date' : 
        {
         'NAME' : 'DATE',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'data di registrazione',
         'MUNIT' : '',
         'DATYP' : 'date',
         },
      
      'accountMoveLine_state' : 
        {
         'NAME' : 'STATE',
         'VARTYPE' : True,
         'DASTR' : '',
         'DESVAR' : 'stato della moveline in termini di validazione',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      
      'accountMoveLine_debit' : 
        {
         'NAME' : 'DARE',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'colonna DARE della partita doppia',
         'MUNIT' : 'euro',
         'DATYP' : 'Decimal',
         },
                
      'accountMoveLine_credit' : 
        {
         'NAME' : 'AVERE',
         'VARTYPE' : False,
         'DASTR' : '',
         'DESVAR' : 'colonna AVERE della partita doppia',
         'MUNIT' : 'euro',
         'DATYP' : 'Decimal',
         }
      }


gv_acc = {
          'accountAccountType_name' : 
            {
             'NAME' : 'LEVA',
             'VARTYPE' : True,
             'DASTR' : '',
             'DESVAR' : 'livello nella struttura dei conti. Contiene una stringa per la descrizione del livello',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
           
          'accountAccount_code' : 
            {
             'NAME' : 'CODA',
             'VARTYPE' : False,
             'DASTR' : '',
             'DESVAR' : 'codice del conto, strutturato in tre livelli',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
          
          'accountAccount_name' : 
            {
             'NAME' : 'NOMA',
             'VARTYPE' : False,
             'DASTR' : '',
             'DESVAR' : 'nome descrittivo del conto',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
          
          'accountAccount_type' : 
            {
             'NAME' : 'TIPA',
             'VARTYPE' : True,
             'DASTR' : '',
             'DESVAR' : 'tipologia del conto',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
         
          'accountAccount_parentName' : 
            {
             'NAME' : 'GENA',
             'VARTYPE' : False,
             'DASTR' : '',
             'DESVAR' : 'nome descrittivo del conto genitore',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
           
          'accountAccount_parentCode' : 
            {
             'NAME' : 'CODG',
             'VARTYPE' : False,
             'DASTR' : '',
             'DESVAR' : 'codice del conto genitore',
             'MUNIT' : '',
             'DATYP' : 'str',
             }

            }

func_dict = {
             'get_account_move_line' : [etl.DbMapping.get_account_move_line, gv_ml],
             #'get_account_move' : data.DbMapping.get_account_move,
             'get_account' : [etl.DbMapping.get_account, gv_acc]
             #'get_partner' : data.DbMapping.get_partner,
             }
#func_run = difflib.get_close_matches(
#comp_run = difflib.get_close_matches(
path = "../config/"
#read csv
reader = csv.reader(open('goal2stark.csv', 'rb'), dialect='excel')
id_file = 0
for row in reader:
    func = row[0]
    comp = row[1]
    # func_dict[func][0] point to function
    df = etl.CreateDF.CreateDF(path, func_dict[func][0], comp)
    # func_dict[func][1] gov dict
    stk_elab = etl.style.style(df, func_dict[func][1])
    stk_elab.DefPathPkl('/tmp/')
    stk_elab.save('stkelab_%i.pickle' %(id_file))
    id_file = id_file + 1
