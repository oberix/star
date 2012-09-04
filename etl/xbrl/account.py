# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Marco Pattaro (<marco.pattaro@servabit.it>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 2 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

__author__ = 'Marco Pattaro (<marco.pattaro@servabit.it>)'
__version__ = '0.1'
__all__ = ['Account']

class Account(object):
    """ An account is an element of a chart of accounts. Usually Accounts are
    linked together in a tree hyerachical structure, where the root is a 'fake'
    account used to hold the whole tree.

    A single account has the following attributes:
        - code: a unique identifier
        - label: a human readeable rappresentation
        - abstract: wether the account can bring a value or not
        - weight: (+1 or -1 or None) sign to use when adding to it's siblings
        - order: order relative to it's siblings
        - balance: ('credit' or 'debit') tells wether the amount was evaluated as
          (credit - debit) or viceversa.
        - period: ('instant' or 'duration') tells if the account is feed during
          the whole fiscal year or else if it's evaluated once at the end of it.
        - parent: the parent Account
        - children: the list of children Accounts
        
    """
    
    def __init__(self, code, label, abstract=False, weight=1, order=0,
                 balance=None, period=None, parent=None, children=[],
                 *args, **kwargs):
        self._code = code
        self.label = label
        self.abstract = abstract
        self.weight = weight
        self.order = order
        self.balance = balance
        self.period = period
        self._parent = None
        self._children = []
        self.parent = parent
        self.children = children

    def __repr__(self):
        ret = "%s \n \
               \tcode: %s\n \
               \tlabel: %s\n \
               \tabstract: %s\n \
               \tweight: %s\n \
               \torder: %s\n \
               \tbalance: %s\n \
               \tperiod: %s\n \
               \tparent: %s\n \
               \tchildren: %s" % \
            (object.__repr__(self), self._code, self.label, self.abstract, 
             self.weight, self.order, self.balance, self.period,
             self.parent is not None and self.parent.code or None, 
             [c.code for c in self._children])
        return ret

    @property
    def code(self):
        return self._code

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        """ Assigne a new parent to the current account """
        if parent is self:
            raise RuntimeError('An Account cannot be parent of itself')
        if self._parent is not parent and self._parent is not None:
            self._parent._remove_child(self)
        self._parent = parent
        if parent is not None and self not in parent.children:
            parent._children.append(self)
            parent._children.sort(key=lambda x : x.order)

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, children):
        """ Assigne a new children list to the current account """
        for child in self._children:
            child.preParent = None
        self._children = []
        for child in children:
            child.parent = self

    def _remove_child(self, child):
        """ Remove given account ad return it
        @ param child: the account obj to remove

        """
        self._children.remove(child)
        child.parent = None

    def isroot(self):
        """ Tell if an account is the root of it's tree """
        return self._parent is None

    def isleaf(self):
        """ Tell if an account is a leaf """
        return len(self._children) == 0
        

if __name__ == '__main__':
    """ jsut a test """
    a1 = Account('a1', 'a1')
    a2 = Account('a2', 'a2', parent=a1)
    a3 = Account('a3', 'a3', parent=a1)
