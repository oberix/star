import sys


# Servabit libraries
sys.path.append('../')
import etl

dict_to_in = {
             'accountAccount_id' : ('id', None), 
             'accountAccount_name' : ('name', None),
             'accountAccount_code' : ('code', None),
             'resCompany_name' : ('company', ('name', None)), 
             'accountAccountType_name' : ('account_type', ('name', None)),
             'accountAccount_type' : ('type', None),
             'accountAccount_parentName' : ('parent', ('name', None)),
             'accountAccount_parentCode' : ('parent', ('code', None))
             }

acc = etl.DBmap2.AccountAccount

dict_out = etl.create_dict.create_dict(acc, dict_to_in)