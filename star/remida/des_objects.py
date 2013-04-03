# -*- coding: utf-8 -*-

################################################################################
#
#    Copyright (C) 2012 Servabit Srl (<infoaziendali@servabit.it>).
#    Author: Luigi Curzi <tremst@gmail.com>
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
################################################################################
import des_filters as dfi
import decimal as dc
import re
import logging
import traceback as trb
import pyparsing as pp
import math
import sys
 
pattern_check_par = r"""
    p=("[^"]+"|'[^']+')
"""
pattern_check_par = re.compile(pattern_check_par, re.IGNORECASE | 
                               re.VERBOSE | re.MULTILINE | re.DOTALL | 
                               re.UNICODE)
                           

def parse_parameter(string_in):
    par = pp.Forward()
    arg = (par | pp.QuotedString("'") | pp.QuotedString('"') | 
           pp.Word(pp.alphanums + "_ -+"))
    args = arg + pp.ZeroOrMore(pp.Suppress(",") + arg)
    filter_w = pp.Word("|", pp.alphanums + "_")
    filter_wo = pp.Combine(pp.Word("|", pp.alphanums + "_") + 
                                   pp.Literal(":")) + pp.Group(args)
    filters = (filter_w ^filter_wo).setParseAction()

    s_par = (pp.Group(pp.Suppress("{{") + 
                      pp.Word(pp.alphas, pp.alphanums + "_ ")\
                        .setParseAction(lambda token: "{{" + token[0] + "}}") + 
                      pp.ZeroOrMore(filters) + pp.Suppress("}}")))
    l_par = (pp.Group(pp.Suppress("{") + pp.Word(pp.nums)\
                        .setParseAction(lambda token: "{" + token[0] + "}") + 
                      pp.ZeroOrMore(filters) + 
                      pp.Suppress("}")))
                     
    par << (s_par ^l_par)
    expr = par + pp.ZeroOrMore(filters)
    if not type(string_in) is unicode:
        string_in = unicode(string_in, "utf8")
    try: 
        parsed_list = expr.parseString(string_in).asList()
    except:
        parsed_list = string_in
    return parsed_list


def evaluate_test_values(string_in, df=None, lp=[]):
    res = u""
    rule_vs_split = string_in.split(",")
    if len(rule_vs_split) == 2:
        rule_vmin = rule_vs_split[0]
        rule_vmax = rule_vs_split[1]
        
        value_min_limit = 0
        if rule_vmin.startswith("["):
            value_min_limit = 1
        value_min = rule_vmin[1:].strip()        
        if value_min == "inf":
            value_min = - sys.maxint -1
        else:
            m = pattern_check_par.match(value_min)
            if m:
                value_min_parsed = parse_parameter(m.groups()[0][1:-1])
                value_min = evaluate_parameter(value_min_parsed, df, lp)
        value_max_limit = 0
        if rule_vmax.endswith("]"):
            value_max_limit = 1
        value_max = rule_vmax[:-1].strip()
        if value_max == "inf":
            value_max = sys.maxint
        else:
            m = pattern_check_par.match(value_max)
            if m:
                value_max_parsed = parse_parameter(m.groups()[0][1:-1])
                value_max = evaluate_parameter(value_max_parsed, df, lp)        
        res = ((value_min, value_min_limit), (value_max, value_max_limit))
    elif len(rule_vs_split) == 1:
        rule_v = rule_vs_split[0]
        
        limit = 1
        if rule_v.startswith("^"):
            limit = 0
            value = rule_v[1:]
        else:
            value = rule_v
        if type(value) is str or type(value) is unicode:
            m = pattern_check_par.match(value)
            if m:
                value_parsed = parse_parameter(m.group()[0][1:-1])
                value = evaluate_parameter(value_parsed, df, lp)             
        res = ((value, limit),)
    return res


def evaluate_parameter(p_parsed, df=None, lp=[]):
    res = u""
    if not type(p_parsed) is list:
        return p_parsed  
    while p_parsed:
        e = p_parsed.pop(0)
        if type(e) is list:
            res = evaluate_parameter(e, df, lp)
        elif e.startswith("|"):
            if e.endswith(":"):
                filter_name = e[1:-1]
                args = []
                args_list = p_parsed.pop(0)
                for arg in args_list:
                    args.append(evaluate_parameter(arg, df, lp))
            else:
                filter_name = e[1:]
                args = []
            des_filter = getattr(dfi, filter_name)
            res = des_filter(res, *args)
        else:
            if e.startswith("{{") and e.endswith("}}"):
                res = df[e[2:-2]][0]
            elif e.startswith("{") and e.endswith("}"):
                res = lp[int(e[1:-1])]
            else:
                res = e
    if type(res) is str:
        res = unicode(res, "utf8")
    return res

    
def propagate_local_parameters(obj, df, lpars):
    if obj.type == "choice":
        try:
            lpars = [evaluate_parameter(parse_parameter(p), df, lpars) 
                     for p in lpars]
        except:
            logging.warning(u"choice '{0}': problema determinazione 'lparameters'"
                            "".format(self))
            lpars = []
        obj.lparameters = lpars
    else:
        obj.lparameters = lpars
    try:
        for child in obj.children:
            propagate_local_parameters(child, df, obj.lparameters)
    except:
        pass
        
        
class Token(object):
    def __init__(self, text, children):
        if not type(text) is unicode:
            text = unicode(text, "utf8")
        self.text = text
        self.children = children
        self.type = "token"
    
    def to_string(self):#, df):
        args = []
        for child in self.children:
            if not child:    
                args.append("")
            else:    
                args.append(child.to_string())
        try:
            args_ = []
            for arg in args:
                if  arg and type(arg) is list or type(arg) is tuple:
                    last = arg[-1]
                    arg_lst = arg[:-1]
                    arg_str = u", ".join([unicode(str(a), "utf8") 
                                          if not type(a) is unicode else a 
                                          for a in arg_lst])
                    if arg_str and len(arg) > 1:
                        arg_str += u" e "
                    arg_str += u"{0}".format(unicode(str(last), "utf8") 
                                             if not type(last) is unicode 
                                             else last)
                    arg = arg_str
                args_.append(arg)
            return self.text.format(*args)
        except:
            # FIXME: raise a warning
            logging.debug(u"{0}".format(trb.format_exc()))
            return self.text


class Rule(object):
    def __init__(self, parameter, values):
        self.parameter = parameter
        self.values = values
        self.lparameters = []
        self.type = "rule"
        
    def check(self, df):
        logging.debug(u"rule '{0}': inizio check ".format(self))
        # FIXME: gestire nodi parent e children
        lparameters = self.lparameters
        logging.debug(u"rule '{0}': parametro='{1}' / parametri locali='{2}'"
                      "".format(self, self.parameter, lparameters))
        
        parameter_parsed = parse_parameter(self.parameter)
        try:
            parameter = evaluate_parameter(parameter_parsed, df, lparameters)
        except:
            logging.warning(u"rule '{0}': problema determinazione 'parameter'"
                            "".format(self))
            parameter = u""
        try:
            test_values = evaluate_test_values(self.values, df, lparameters)
        except:
            logging.warning(u"rule '{0}': problema determinazione 'test_values'"
                            "".format(self))
            test_values = u""
        if len(test_values) == 2:
            value_min = test_values[0][0]
            value_min_limit = test_values[0][1]
            value_max = test_values[1][0]
            value_max_limit = test_values[1][1]
            try:
                value_min = dc.Decimal(str(value_min))
                value_max = dc.Decimal(str(value_max))
                parameter = dc.Decimal(str(parameter))
                if math.isnan(parameter):
                    return False                
            except:
                value_min = str(value_min)
                value_max = str(value_max)
                parameter = str(parameter)
            limits = (value_min_limit, value_max_limit)
            logging.debug(u"rule '{0}': parametro='{1}' / vmin='{2}' / vmax='{3}' / "
                          "criteri='{4}".format(self, parameter, value_min, 
                                                value_max, limits))
            if limits == (0,0) and value_min < parameter < value_max:
                logging.debug(u"rule '{0}': verificata".format(self))
                return True
            elif limits == (1,0) and value_min <= parameter < value_max:
                logging.debug(u"rule '{0}': verificata".format(self))
                return True
            elif limits == (0,1) and value_min < parameter <= value_max:
                logging.debug(u"rule '{0}': verificata".format(self))
                return True
            elif limits == (1,1) and value_min <= parameter <= value_max:
                logging.debug(u"rule '{0}': verificata".format(self))
                return True
        elif len(test_values) == 1:
            value = test_values[0][0]
            try:
                value = dc.Decimal(str(value))
                parameter = dc.Decimal(str(parameter))
                if math.isnan(parameter):
                    return False
            except:
                value = str(value)
                parameter = str(parameter)    
            limit = test_values[0][1]
            logging.debug(u"rule '{0}': parametro='{1}' / valore='{2}' / criterio='{3}"
                          "".format(self, parameter, value, limit))
            if limit == 1 and value == parameter:
                logging.debug(u"rule '{0}': verificata".format(self))
                return True
            if limit == 0 and value != parameter:
                logging.debug(u"rule '{0}': verificata".format(self))
                return True
            
        logging.debug(u"rule '{0}': non verificata".format(self))
        return False
    
    
class Option(object):
    def __init__(self, rules, token):
        self.rules = rules
        self.token = token
        self.children = [r for r in self.rules if r]
        self.children.append(self.token)
        self.lparameters = []
        self.type = "option"
    
    def check(self, df):
        logging.debug(u"option '{0}': inizio check".format(self))
        for rule in self.rules:
            if not rule.check(df):
                logging.debug(u"option '{0}': non verificata".format(self))
                return False  
        logging.debug(u"option '{0}': verificata".format(self))
        return True

    def to_string(self):
        return self.token.to_string()


class Choice(object):
    def __init__(self, options, df, lparameters=[]):
        self.options = options
        self.children = [o for o in self.options if o]
        self.lparameters = lparameters
        self.dataframe = df
        self.type = "choice"
        
    def to_string(self):
        logging.debug(u"choice '{0}': inizio sostituzione".format(self))
        if self.lparameters:
            propagate_local_parameters(self, self.dataframe, self.lparameters)
        res = ""
        for opt in self.options:
            if opt.check(self.dataframe):
                res = opt.to_string()
                break
        logging.debug(u"choice '{0}': fine sostituzione".format(self))
        return res

    
class Placeholder(object):
    def __init__(self, parameter, df):
        self.parameter = parameter
        self.lparameters = []
        self.dataframe = df
        self.type = "placeholder"
        
    def to_string(self):
        logging.debug(u"placeholder '{0}': inizio sostituzione".format(self))
        lparameters = self.lparameters
        parameter_parsed = parse_parameter(self.parameter)
        try:
            arg = evaluate_parameter(parameter_parsed, self.dataframe, lparameters)
        except:
            logging.warning(u"placeholder '{0}': problema determinazione 'arg'"
                            "".format(self))            
            arg = u""
        if arg and type(arg) is list or type(arg) is tuple:
            last = arg[-1]
            arg_lst = arg[:-1]
            arg_str = u", ".join([unicode(str(a), "utf8") 
                                  if not type(a) is unicode else a 
                                  for a in arg_lst])
            if arg_str and len(arg) > 1:
                arg_str += u" e "
            arg_str += u"{0}".format(unicode(str(last), "utf8") 
                                     if not type(last) is unicode 
                                     else last)
            arg = arg_str
        res = u"{0}".format(arg)
        logging.debug(u"placeholder '{0}': fine sostituzione".format(self))
        return res


class FormattedText(object):
    TAGS = ("bold", "italic", "underline", "sub", "sup", "newline", "title", 
            "uppercase", "plain")
    
    def __init__(self, tag="plain", text="", children=[], parent=None):
        if not tag in self.TAGS:
            # FIXME: raise a warning
            tag = "plain"
        self.tag = tag
        if not type(text) is unicode:
            text = unicode(text, "utf8")
        self.text = text
        self.children = children
        self.lparameters = []
        self.type = "formatted_text"
        
    def set_bold(self, string_in):
        return u"\\textbf{{{0}}}".format(string_in)
            
    def set_italic(self, string_in):
        return u"\\textit{{{0}}}".format(string_in)

    def set_underline(self, string_in):
        return u"\\underline{{{0}}}".format(string_in)
        
    def set_sup(self, string_in):
        return u"$^{{{0}}}$".format(string_in)

    def set_sub(self, string_in):
        return u"$_{{{0}}}$".format(string_in)

    def set_newline(self, string_in):
        return u"\\newline "
    
    def set_title(self, string_in):
        return u"{0}".format(string_in[0].upper() + string_in[1:])
    
    def set_upper(self, string_in):
        return u"{0}".format(string_in.upper())
    
    def set_plain(self, string_in):
        return string_in
    
    def to_string(self):
        logging.debug(u"formattedtext '{0}': inizio sostituzione".format(self))
        args = []
        
        for child in self.children:
            if not child:    
                args.append("")
            else:
                args.append(child.to_string())
        set_format = getattr(self, "set_{0}".format(self.tag))
        try:
            args_ = []
            for arg in args:
                if  arg and type(arg) is list or type(arg) is tuple:
                    last = arg[-1]
                    arg_lst = arg[:-1]
                    arg_str = u", ".join([unicode(str(a), "utf8") 
                                          if not type(a) is unicode else a 
                                          for a in arg_lst])
                    if arg_str and len(arg) > 1:
                        arg_str += u" e "
                    arg_str += u"{0}".format(unicode(str(last), "utf8") 
                                             if not type(last) is unicode 
                                             else last)
                    arg = arg_str
                args_.append(arg)
            res = set_format(self.text.format(*args))
            logging.debug(u"formattedtext '{0}': fine sostituzione".format(self))
        except:
            # FIXME: raise a warning
            logging.debug(u"{0}".format(trb.format_exc()))
            res = set_format(self.text)
            logging.debug(u"formattedtext '{0}': fine sostituzione".format(self))
        return res

