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

__VERSION__ = '0.1'
__AUTHOR__ = 'Luigi Cirillo (<luigi.cirillo@servabit.it>)'


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql
from datetime import datetime
from decimal import Decimal

import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, Sequence, ForeignKey, Date, Boolean
import logging



# Servabit libraries
sys.path.append('../')


Base = declarative_base()
conf_goal = None
logger = None

class IrSequence(Base):
    __tablename__ = 'ir_sequence'
    
    name = Column(String(64), nullable=False)
    code = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    
    #one2many
    journals = relationship("AccountJournal")
    
    @staticmethod
    def getVatSequencesNames(cls,session,company_id):
        sequences=session.query(cls).filter(cls.code=='RIVA',cls.company_id==company_id).all()
        names=[]
        for s in sequences:
            names.append(s.name)
        return names


class ResCompany(Base):
    __tablename__ = 'res_company'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    #one2one
    partner = relationship("ResPartner",  primaryjoin="ResCompany.partner_id==ResPartner.id", uselist=False)
    ateco_2007_vat_activity = Column(String(300))
    
    @staticmethod
    def getCompanyTaxCode(cls,session,company_id):
        if not company_id:
            return False
        company=session.query(cls).filter(cls.id==company_id).first()
        if not company:
            return False
        return company.partner.tax
    
    #method called from reports
    @staticmethod
    def getCompanyHeaderTex(cls,session,company_id):
        if not company_id:
            return False
        company=session.query(cls).filter(cls.id==company_id).first()
        if not company:
            return False
        header=company.name
        if company.partner.addresses[0].street:
            header+='\\\\'+company.partner.addresses[0].street
        if company.partner.addresses[0].zip:
            header+='\\\\'+company.partner.addresses[0].zip
        if company.partner.addresses[0].city:
            header+=' '+company.partner.addresses[0].city
        if company.partner.vat:
            header+='\\\\P. IVA '+company.partner.vat
        return header

    
class ResPartner(Base):
    __tablename__ = 'res_partner'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    vat = Column(String(32))
    tax = Column(String(36))
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=True)
    
    #one2one
    company = relationship("ResCompany", primaryjoin="ResCompany.id==ResPartner.company_id")
    #one2many
    addresses = relationship("ResPartnerAddress")
    
    
class ResPartnerAddress(Base):
    __tablename__ = 'res_partner_address'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    street = Column(String(128))
    city = Column(String(128))
    zip = Column(String(24))
    
    #many2one
    partner = relationship("ResPartner")
        
        
class AccountFiscalyear(Base):
    __tablename__ = 'account_fiscalyear'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    date_start = Column(Date, nullable=False)
    date_stop = Column(Date, nullable=False)
    
    #one2many
    periods = relationship("AccountPeriod")
    
    
    @staticmethod
    def findYearBefore(cls,session,fiscalyear_id):
        '''
        Return the year before current.
        '''
        if not fiscalyear_id:
            return False
            
        current_year=session.query(cls).filter(cls.id==fiscalyear_id).first()
        previous_year_date_start=current_year.date_start.replace(year=current_year.date_start.year-1)
        previous_year=session.query(cls).filter(cls.date_start==previous_year_date_start,cls.company_id==current_year.company_id).first()
        return previous_year
    
    
class AccountPeriod(Base):
    __tablename__ = 'account_period'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    date_start = Column(Date, nullable=False)
    date_stop = Column(Date, nullable=False)
    special = Column(Boolean)
    
    fiscalyear_id = Column(Integer, ForeignKey('account_fiscalyear.id'), nullable=False)
    fiscalyear = relationship("AccountFiscalyear")
    
    @staticmethod
    def getNormalPeriods(cls,session,date,company_id):
        return session.query(cls).filter(cls.date_start<=date,cls.date_stop>=date,cls.company_id==company_id,cls.special==False).all()
        
    '''
    returns period_ids of periods preceding the period passed as argument until x year (ex. 1 trim. 2012 (x=1) -> [1 trim. 2011, 2 trim 2011, 3 trim 2011, 4 trim 2011])
    '''
    @staticmethod
    def getPreviousPeriodIdsUntilXyears(cls, session, period_id, x, company_id):
        period=session.query(cls).filter(cls.id==period_id).first()
        search_period_datestart=period.date_start.replace(year=period.date_start.year-x)
        
        previous_period_ids=[]
        previous_periods=session.query(AccountPeriod).filter(AccountPeriod.date_start>=search_period_datestart,AccountPeriod.date_stop<period.date_stop,AccountPeriod.company_id==company_id,cls.special==False).all()
        for p in previous_periods:
            previous_period_ids.append(p.id)
        return previous_period_ids


class AccountAccountType(Base):
    __tablename__ = 'account_account_type'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    code = Column(String(32), nullable=False)
    

class AccountAccount(Base):
    __tablename__ = 'account_account'
    
    name = Column(String(128), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    code = Column(String(64))
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    user_type = Column(Integer, ForeignKey('account_account_type.id'), nullable=False)
    type = Column(String(16), nullable=False)
    parent_id = Column(Integer, ForeignKey('account_account.id'))
    account_type = relationship("AccountAccountType")
    company = relationship("ResCompany")
    parent = relationship("AccountAccount", remote_side=[id])
    
    @staticmethod
    def computeBalance(cls, account, debit=Decimal('0.00'), credit=Decimal('0.00')):
        '''
        this function calculates the balance (starting from debit and credit amounts) according to the internal type of the account
        @param account: it's an instance of AccountAccount
        @param debit: it's a float (or int or Decimal)
        @param credit: it's a float (or int or Decimal)
        returns a Decimal
        '''
        result=None
        if account.account_type.code in ['ammor','income','nasset','otherdebs','payable']:
            result=Decimal(credit)-Decimal(debit)
        elif account.account_type.code in ['asset','expense','otherass','receivable']:
            result=Decimal(debit)-Decimal(credit)
        return result

    @staticmethod
    def computeAmount(cls, session, account, totals, dateStart, dateEnd,  onlyValidatedMoveLines=True):
        '''
        @param totals: is a list of strings. (considered values: 'debit', 'credit', 'balance')
        @param account: it's an instance of AccountAccount
        returns amounts of 'debit' and/or 'credit' and/or 'balance' of the account passed as parameter from dateStart to dateEnd (including both)
        '''
        moveLines=[]
        if onlyValidatedMoveLines:
            moveLines=session.query(AccountMoveLine).join(AccountMove).filter(\
                                AccountMoveLine.account_id==account.id,\
                                AccountMoveLine.date>=dateStart,\
                                AccountMoveLine.date<=dateEnd,\
                                AccountMove.state=='posted',\
                                ).all()
        else:
            moveLines=session.query(AccountMoveLine).filter(\
                                    AccountMoveLine.account_id==account.id,\
                                    AccountMoveLine.date>=dateStart,\
                                    AccountMoveLine.date<=dateEnd,\
                                    ).all()
                                    
        debitTotal=Decimal(0)
        creditTotal=Decimal(0)
        for line in moveLines:
            if line.debit:
                debitTotal+=line.debit
            if line.credit:
                creditTotal+=line.credit
        results={}
        if totals.count('debit')>0:
            results['debit']=debitTotal
        if totals.count('credit')>0:
            results['credit']=creditTotal
        if totals.count('balance')>0:
            results['balance']=cls.computeBalance(cls, account, debitTotal, creditTotal)
            
        return results


class AccountJournal(Base):
    __tablename__ = 'account_journal'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    type = Column(String(32), nullable=False)
    
    sequence_id = Column(Integer, ForeignKey('ir_sequence.id'), nullable=False)
    sequence = relationship("IrSequence")


class AccountTax(Base):
    __tablename__ = 'account_tax'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'))
    
    tax_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    base_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    ref_tax_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    ref_base_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    
    
class AccountTaxCode(Base):
    __tablename__ = 'account_tax_code'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True, )

class AccountVoucher(Base):
    __tablename__ = 'account_voucher'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    
    company_id = Column(Integer, ForeignKey('res_company.id'))
    period_id = Column(Integer, ForeignKey('account_period.id'))
    move_id = Column(Integer, ForeignKey('account_move.id'))
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    date = Column(Date)
    date_due = Column(Date)
    number = Column(String(32))
    state = Column(String(32))
    type = Column(String(16))
    amount = Column(postgresql.NUMERIC, nullable=False)

    partner = relationship("ResPartner",  uselist=False)
    move = relationship("AccountMove",  uselist=False)

class AccountInvoice(Base):
    __tablename__ = 'account_invoice'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    
    company_id = Column(Integer, ForeignKey('res_company.id'))
    period_id = Column(Integer, ForeignKey('account_period.id'))
    move_id = Column(Integer, ForeignKey('account_move.id'))
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    date_document = Column(Date, nullable=False)
    date_due = Column(Date)
    number = Column(String(64))
    state = Column(String(16))
    type = Column(String(16))
    amount_total = Column(postgresql.NUMERIC)
    
    move = relationship("AccountMove",  uselist=False)
    partner = relationship("ResPartner",  uselist=False)

    
class AccountMove(Base):
    __tablename__ = 'account_move'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    ref = Column(String(64))
    state = Column(String(16), nullable=False)
    company_id = Column(Integer, ForeignKey('res_company.id'))
    journal_id = Column(Integer, ForeignKey('account_journal.id'), nullable=False)
    period_id = Column(Integer, ForeignKey('account_period.id'), nullable=False)
    date = Column(Date, nullable=False)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    partner = relationship("ResPartner",  uselist=False)
    invoice = relationship("AccountInvoice",  uselist=False)
    to_check = Column(Boolean)
    #amount = Column(Float)
    #one2many
    move_lines = relationship("AccountMoveLine")
    company = relationship("ResCompany")
    period = relationship("AccountPeriod")
    journal = relationship("AccountJournal")
    
    def _get_date_document(self):
        res=False
        if self.invoice:
            res=self.invoice.date_document           
        return res
    
class AccountMoveLine(Base):
    __tablename__ = 'account_move_line'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    ref = Column(String(64))
    state = Column(String(16))
    
    company_id = Column(Integer, ForeignKey('res_company.id'))
    journal_id = Column(Integer, ForeignKey('account_journal.id'), nullable=False)
    period_id = Column(Integer, ForeignKey('account_period.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account_account.id'), nullable=False)
    move_id = Column(Integer, ForeignKey('account_move.id'), nullable=False)
    tax_code_id = Column(Integer, ForeignKey('account_tax_code.id'), nullable=False)
    
    reconcile_id = Column(Integer, ForeignKey('account_move_reconcile.id'), nullable=False)
    reconcile = relationship("AccountMoveReconcile", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_id")
    
    reconcile_partial_id = Column(Integer, ForeignKey('account_move_reconcile.id'), nullable=False)
    reconcile_partial = relationship("AccountMoveReconcile", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_partial_id")
    
    partner_id = Column(Integer, ForeignKey('res_partner.id'))
    
    date = Column(Date, nullable=False)
    date_maturity = Column(Date)
    debit = Column(postgresql.NUMERIC)
    credit = Column(postgresql.NUMERIC)
    tax_amount = Column(postgresql.NUMERIC)
    
    #many2one
    move = relationship("AccountMove")
    journal = relationship("AccountJournal")
    account = relationship("AccountAccount")
    partner = relationship("ResPartner")
    company = relationship("ResCompany")
    period = relationship("AccountPeriod")
    
class AccountMoveReconcile(Base):
    __tablename__ = 'account_move_reconcile'
    
    name = Column(String(64), nullable=False)
    type = Column(String(16), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    
    lines = relationship("AccountMoveLine", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_id")
    partial_lines = relationship("AccountMoveLine", primaryjoin="AccountMoveReconcile.id==AccountMoveLine.reconcile_partial_id")


'''
Initialize:
    conf_goal2d : protected hold conf_goaluaration informations
    logger : private, log instance
'''
    

def log_istance():
    global conf_goal, logger
    log_istance =  'DBMapping'
    logging.basicConfig(level = conf_goal.options.get('log_level'))
    logger = logging.getLogger('DBMapping')
    

    
def open_session():
    '''
    open a database session from informations holded by conf_goal2d
    '''
    global conf_goal, logger
    logger.debug('Opening session')
    Session = sessionmaker(bind = create_engine( \
        conf_goal.options.get('dbtype') + '+' + \
        conf_goal.options.get('driver') + '://' + \
        conf_goal.options.get('user') + ':' + \
        conf_goal.options.get('pwd') + '@' + \
        conf_goal.options.get('host') + '/' + \
        conf_goal.options.get('dbname')))
    return Session()

def close_session(session,):
    '''
    Close database session
    '''
    global logger
    logger.debug('Closing session')
    session.close_all()

def get_account_move_line(name_comp):
    '''
    id_comp : id company on database
    return a dataframe with move lines of the company
    '''
    global conf_goal, logger
    log_istance()
    session = open_session()
    comp = session.query(ResCompany).filter_by( \
            name = name_comp \
            ).first()
    logger.info('Extracting account_move_line for %s' % (comp.name))
    data = {'accountMoveLine_id' : [], 'accountMove_name' : [], \
            'accountMoveLine_ref' : [], 'accountMoveLine_date' : [], \
            'accountPeriod_name' : [], 'resPartner_name' : [], \
            'accountAccount_name' : [], 'accountMoveLine_name' : [], \
            'accountJournal_name' : [], 'accountMoveLine_debit' : [], \
            'accountMoveLine_credit' : [], 'accountMoveLine_state' : [], \
            'accountMoveReconcile_name' : [], 'accountTax_name' : [], 
            'accountAccount_code' : []}
    for aml in session.query(\
            AccountMoveLine\
            ).filter_by(company_id = comp.id).all():
        data['accountMoveLine_id'].append(aml.id)
        
        if (aml.move != None):
            data['accountMove_name'].append(aml.move.name)
        else:
            data['accountMove_name'].append(None)
        data['accountMoveLine_ref'].append(aml.ref)
        data['accountMoveLine_date'].append(aml.date)
        if (aml.period != None):
            data['accountPeriod_name'].append(aml.period.name)
        else:
            data['accountPeriod_name'].append(None)
        if (aml.partner != None):
            data['resPartner_name'].append(aml.partner.name)
        else:
            data['resPartner_name'].append(None)
        if (aml.account != None):
            data['accountAccount_name'].append(aml.account.name)
            data['accountAccount_code'].append(aml.account.code)
        else:
            data['accountAccount_name'].append(None)
            data['accountAccount_code'].append(None)
        data['accountMoveLine_name'].append(aml.name)
        if (aml.journal != None):
            data['accountJournal_name'].append(aml.journal.name)
        else:
            data['accountJournal_name'].append(None)
        data['accountMoveLine_debit'].append(aml.debit)
        data['accountMoveLine_credit'].append(aml.credit)
        data['accountMoveLine_state'].append(aml.state)
        if (aml.reconcile != None):
            data['accountMoveReconcile_name'].append(aml.reconcile.name)
        else:
            data['accountMoveReconcile_name'].append(None)
        if (aml.tax_code_id != None):
            #import ipdb; ipdb.set_trace()
            tax = session.query( \
                                 AccountTax \
                    ).filter_by(tax_code_id = aml.tax_code_id).first()
            if (tax == None):
                tax = session.query( \
                AccountTax).filter_by(base_code_id = \
                aml.tax_code_id).first()
                if (tax == None):
                    tax = session.query( \
                                         AccountTax \
                    ).filter_by(ref_tax_code_id = \
                    aml.tax_code_id).first()
                    if (tax == None):
                        tax = session.query( \
                                             AccountTax \
                        ).filter_by(ref_base_code_id = \
                        aml.tax_code_id).first()
            if (tax != None):
                data['accountTax_name'].append(tax.name)
            else:
                data['accountTax_name'].append(None)
        else:
            data['accountTax_name'].append(None)
    close_session(session)
    return data

def get_account_move(name_comp):
    '''
    id_comp : id company on database
    return a dataframe with move of the company
    '''
    global conf_goal, logger
    log_istance()
    session = open_session()
    comp = session.query(ResCompany).filter_by( \
            name = name_comp \
            ).first()
    logger.info('Extracting account_move for %s' % (comp.name))
    data = {'accountMove_id' : [], 'accountMove_name' : [], \
            'accountMove_ref' : [], 'accountMove_date' : [], \
            'accountPeriod_name' : [], 'accountJournal_name' : [], \
            'resCompany_name' : [], 'resPartner_name' : [] ,\
            'accountMove_toCheck' : [], 'accountMove_state' : []}
    for am in session.query(AccountMove).filter_by( \
                company_id = comp.id \
                ).all():
        data['accountMove_id'].append(am.id)
        data['accountMove_name'].append(am.name)
        data['accountMove_ref'].append(am.ref)
        data['accountMove_date'].append(am.date)
        
        if (am.period != None):
            data['accountPeriod_name'].append(am.period.name)
        else:
            data['accountPeriod_name'].append(None)

        data['accountJournal_name'].append(am.journal.name)
        
        if (am.company_id != None):
            data['resCompany_name'].append(am.company.name)
        else:
            data['resCompany_name'].append(None)
        
        if (am.partner != None):
            data['resPartner_name'].append(am.partner.name)
        else:
            data['resPartner_name'].append(None)
            
        if (am.to_check != None):
            data['accountMove_toCheck'].append(am.to_check)
        else:
            data['accountMove_toCheck'].append(None)
        data['accountMove_state'].append(am.state)
    close_session(session)
    return data

def get_account(name_comp):
    '''
    id_comp : id company on database
    return a dataframe with accounts of the company
    '''
    global conf_goal, logger
    log_istance()
    session = open_session()
    comp = session.query(ResCompany).filter_by( \
            name = name_comp \
            ).first()
    logger.info('Extracting account for %s' % (comp.name))
    data = {'accountAccount_id' : [], 'accountAccount_name' : [], \
        'accountAccount_code' : [], 'resCompany_name' : [], \
        'accountAccountType_name' : [], 'accountAccount_type' : [], \
        'accountAccount_parentName' : [], 'accountAccount_parentCode' : []}
    for acc in session.query( \
                AccountAccount \
                ).filter_by(company_id = comp.id).all():
        data['accountAccount_id'].append(acc.id)
        data['accountAccount_name'].append(acc.name)
        data['accountAccount_code'].append(acc.code)
        data['resCompany_name'].append(acc.company.name)
        data['accountAccountType_name'].append(acc.account_type.name)
        data['accountAccount_type'].append(acc.type)
        if (acc.parent_id != None):
            data['accountAccount_parentName'].append(acc.parent.name)
            data['accountAccount_parentCode'].append(acc.parent.code)
        else:
            data['accountAccount_parentName'].append(None)
            data['accountAccount_parentCode'].append(None)
    close_session(session)
    return data

def get_partner(name_comp):
    '''
    id_comp : id company on database
    return a dataframe with move partners of the company
    '''
    global conf_goal, logger
    log_istance()
    session = open_session()
    comp = session.query(ResCompany).filter_by( \
            name = name_comp \
            ).first()
    logger.info('Extracting partner for %s' % (comp.name))
    data = {'resPartner_id' : [], 'resPartner_name' : [], \
            'resPartner_tax' : [], 'resPartner_vat' : [], \
            'resCompany_name' : []}
    id_comp = comp.name
    for par in session.query(ResPartner).filter_by( \
            company_id = id_comp \
            ).all():
        data['resPartner_id'].append(par.id)
        data['resPartner_name'].append(par.name)
        data['resPartner_tax'].append(par.tax)
        data['resPartner_vat'].append(par.vat)
        if (par.company != None):
            data['resCompany_name'].append(par.company.name)
        else:
            data['resCompany_name'].append(None)
    close_session(session)
    return data
