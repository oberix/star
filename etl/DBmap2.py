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
BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))
from share import config

Base = declarative_base()
filepath = '/home/lcirillo/sviluppo/svn/star/trunk/config/DbConfig.cfg'
conf = config.Config(filepath)
conf.parse()
log_istance =  'DBMapping'
logging.basicConfig(level = conf.options.get('log_level'))
logger = logging.getLogger('DBMapping')


class IrSequence(Base):
    __tablename__ = 'ir_sequence'
    
    name = Column(String(64), nullable=False)
    code = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=False)
    
    #one2many
    journals = relationship("AccountJournal")
    
    
class ResCompany(Base):
    __tablename__ = 'res_company'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    #one2one
    partner = relationship("ResPartner",  primaryjoin="ResCompany.partner_id==ResPartner.id", uselist=False)
    ateco_2007_vat_activity = Column(String(300))
    
        
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


def open_session():
    '''
    open a SQLAlchemy session from informations holded by conf_goal2d
    '''
    global conf, logger
    logger.debug('Opening session')
    #import ipdb; ipdb.set_trace()
    Session = sessionmaker(bind = create_engine( \
        conf.options.get('dbtype') + '+' + \
        conf.options.get('driver') + '://' + \
        conf.options.get('user') + ':' + \
        conf.options.get('pwd') + '@' + \
        conf.options.get('host') + '/' + \
        conf.options.get('dbname')))
    return Session()

def close_session(session,):
    '''
    Close SQLAlchemy session
    '''
    global logger
    logger.debug('Closing session')
    session.close_all()
