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



'''
Created on 12/lug/2012

@author: lcirillo
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import postgresql
from datetime import datetime
from decimal import Decimal

import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, Sequence, ForeignKey, Date, Boolean, Float
import logging

Base = declarative_base()


class ResCompany(Base):
    __tablename__ = 'res_company'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('res_company_seq'), primary_key=True)
    partner_id = Column(Integer, ForeignKey('res_partner.id'), nullable=False)
    #one2one
    partner = relationship("ResPartner",  primaryjoin="ResCompany.partner_id==ResPartner.id", uselist=False)
    ateco_2007_vat_activity = Column(String(300))
    
        
class ResPartner(Base):
    __tablename__ = 'res_partner'
    
    name = Column(String(64), nullable=False)
    id = Column(Integer, Sequence('res_partner_seq'), primary_key=True)
    vat = Column(String(32))
    tax = Column(String(36))
    company_id = Column(Integer, ForeignKey('res_company.id'), nullable=True)
    
    #one2one
    company = relationship("ResCompany", primaryjoin="ResCompany.id==ResPartner.company_id")
    #one2many
    #addresses = relationship("ResPartnerAddress")
    

class CrmLead(Base):
    __tablename__ = 'crm_lead'
    
    name = Column(String(64))
    id = Column(Integer, Sequence('crm_lead_seq'), primary_key=True)
    create_date = Column(Date)
    contact_name = Column(String(64))
    
    partner_id = Column(Integer, ForeignKey('res_partner.id'))
    partner = relationship("ResPartner")
    
    date_action = Column(Date)
    title_action = Column(String(64))
    
    stage_id = Column(Integer, ForeignKey('crm_case_stage.id'))
    stage = relationship("CrmCaseStage")
    
    planned_revenue = Column(postgresql.DOUBLE_PRECISION)
    probability = Column(postgresql.DOUBLE_PRECISION)

    user_id = Column(Integer, ForeignKey('res_users.id'))
    user = relationship("ResUsers")
    
    state = Column(String(16))

   
class CrmCaseStage(Base):
    __tablename__ = 'crm_case_stage'
    
    id = Column(Integer, Sequence('crm_case_stage_seq'), primary_key=True)
    name = Column(String(64), nullable=False)
    
class ResUsers(Base):
    __tablename__ = 'res_users'
    
    id = Column(Integer, Sequence('res_users_seq'), primary_key=True)
    name = Column(String(64), nullable=False)
    


    