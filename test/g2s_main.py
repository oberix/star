import sys
import difflib

# Servabit libraries
sys.path.append('../')
import data

path_cvs = 'goal2stark.csv'
func_ls = ['get_account_move_line', 'get_account_move', 'get_account', 'get_partner',]
comp_ls = ['Rete Servabit','Servabit','Studiabo','Vicem','Aderit']
func_dict = {
             'get_account_move_line' : [data.DbMapping.get_account_move_line, gv_ml],
                                        
             'get_account_move' : data.DbMapping.get_account_move,
             'get_account' : data.DbMapping.get_account,
             'get_partner' : data.DbMapping.get_partner,
             }
#func_run = difflib.get_close_matches(
#comp_run = difflib.get_close_matches(
path = "../config/"
df = data.CreateDF.CreateDF(path, data.DbMapping.get_account_move_line, 3)
gv = {
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
stk_elab = data.style.style(df, gv)