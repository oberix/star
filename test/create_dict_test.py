import sys


# Servabit libraries
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
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
