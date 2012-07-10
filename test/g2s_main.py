import sys
import difflib

# Servabit libraries
sys.path.append('../')
import data
import csv

path_cvs = 'goal2stark.csv'
func_ls = ['get_account_move_line', 'get_account_move', 'get_account', 'get_partner',]
comp_ls = ['Rete Servabit','Servabit','Studiabo','Vicem','Aderit']

gv_ml = {
      'accountAccount_code' : 
        {
         'NAME' : 'CODA',
         'AGGREG' : True,
         'DASTR' : '',
         'DESVAR' : 'codice identificativo del conto',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      
      'accountAccount_name' : 
        {
         'NAME' : 'NOMA',
         'AGGREG' : False,
         'DASTR' : '',
         'DESVAR' : 'nome descrittivo del conto',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      
      'accountMoveLine_date' : 
        {
         'NAME' : 'DATE',
         'AGGREG' : False,
         'DASTR' : '',
         'DESVAR' : 'data di registrazione',
         'MUNIT' : '',
         'DATYP' : 'date',
         },
      
      'accountMoveLine_state' : 
        {
         'NAME' : 'STATE',
         'AGGREG' : True,
         'DASTR' : '',
         'DESVAR' : 'stato della moveline in termini di validazione',
         'MUNIT' : '',
         'DATYP' : 'str',
         },
      
      'accountMoveLine_debit' : 
        {
         'NAME' : 'DARE',
         'AGGREG' : False,
         'DASTR' : '',
         'DESVAR' : 'colonna DARE della partita doppia',
         'MUNIT' : 'euro',
         'DATYP' : 'Decimal',
         },
                
      'accountMoveLine_credit' : 
        {
         'NAME' : 'AVERE',
         'AGGREG' : False,
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
             'AGGREG' : True,
             'DASTR' : '',
             'DESVAR' : 'livello nella struttura dei conti. Contiene una stringa per la descrizione del livello',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
           
          'accountAccount_code' : 
            {
             'NAME' : 'CODA',
             'AGGREG' : False,
             'DASTR' : '',
             'DESVAR' : 'codice del conto, strutturato in tre livelli',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
          
          'accountAccount_name' : 
            {
             'NAME' : 'NOMA',
             'AGGREG' : False,
             'DASTR' : '',
             'DESVAR' : 'nome descrittivo del conto',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
          
          'accountAccount_type' : 
            {
             'NAME' : 'TIPA',
             'AGGREG' : True,
             'DASTR' : '',
             'DESVAR' : 'tipologia del conto',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
         
          'accountAccount_parentName' : 
            {
             'NAME' : 'GENA',
             'AGGREG' : False,
             'DASTR' : '',
             'DESVAR' : 'nome descrittivo del conto genitore',
             'MUNIT' : '',
             'DATYP' : 'str',
             },
           
          'accountAccount_parentCode' : 
            {
             'NAME' : 'CODG',
             'AGGREG' : False,
             'DASTR' : '',
             'DESVAR' : 'codice del conto genitore',
             'MUNIT' : '',
             'DATYP' : 'str',
             }

            }

func_dict = {
             'get_account_move_line' : [data.DbMapping.get_account_move_line, gv_ml],
             #'get_account_move' : data.DbMapping.get_account_move,
             'get_account' : [data.DbMapping.get_account, gv_acc]
             #'get_partner' : data.DbMapping.get_partner,
             }
#func_run = difflib.get_close_matches(
#comp_run = difflib.get_close_matches(
path = "../config/"
reader = csv.reader(open('goal2stark.csv', 'rb'), dialect='excel')
id_file = 0
for row in reader:
    func = row[0]
    comp = row[1]
    df = data.CreateDF.CreateDF(path, func_dict[func][0], comp)
    stk_elab = data.style.style(df, func_dict[func][1])
    stk_elab.DefPathPkl('/tmp/')
    stk_elab.Dumpk('stkelab_%i.pickle' %(id_file))
    id_file = id_file + 1