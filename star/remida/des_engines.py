# -*- coding: utf-8 -*-

###############################################################################
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
###############################################################################

import des_objects as dob
from xml.etree.ElementTree import fromstring


class xml_engine(object):
    FORMAT_TAGS = {"b": "bold", "i": "italic", "u": "underline", "sub": "sub",
                   "sup": "sup", "br": "newline", "title": "title",
                   "upper": "uppercase"}

    def __init__(self, main_string="", portfolio_string="", dataframe=None):
        self.main = fromstring(main_string.encode("utf8"))
        self.portfolio = fromstring(portfolio_string.encode("utf8"))
        self.dataframe = dataframe
        self.choices = self.parse_choices()

    def clean(self, string_in):
        # togliamo gli spazi vuoti e le newline iniziali e finali
        if not type(string_in) is unicode:
            string_in = unicode(string_in, "utf8")
        string_out = string_in.strip("\n")
        # dividiamo in righe
        lines = string_out.splitlines()
        for i in xrange(len(lines)):
            lines[i] = unicode(" ", "utf8").join(lines[i].split())
        return unicode(" ", "utf8").join(lines)
    
    def parse_placeholders(self, parent):
        return parent.findall("placeholder")

    def parse_choices(self):
        e_chs = self.portfolio.findall("choice")
        
        res = {}
        for e_ch in e_chs:
            id_ = e_ch.get("id", "")
            if not id_:
                # FIXME: raise a warning
                continue
            res[id_] = e_ch
        return res

    def create_placeholder_obj(self, ph):
        lpars = ph.get("p", "")
        lpars_split = lpars.split(";")
        if len(lpars_split) == 0:
            # FIXME: raise warning
            return None
        if len(lpars_split) > 1:
            # FIXME: raise warning
            pass
        parameter = lpars_split[0]
        return dob.Placeholder(parameter, self.dataframe)
            
    def create_token_obj(self, ph):
        b_text = ph.text or ""
        a_text = ph.tail or ""
        children_text = []
        nodes = []
        for i, child in enumerate(ph.getchildren()):
            children_text.extend(["{{{0}}}".format(i), child.tail or ""])
            if child.tag == "placeholder":
                if child.get("t", "sub") == "sub":
                    obj = self.create_placeholder_obj(child)
                else:
                    obj = self.create_choice_obj(child)
            else:
                obj = self.create_formattedtext_obj(child)
            nodes.append(obj)
        text = b_text + "".join(children_text) + a_text
        return dob.Token(self.clean(text), nodes)
        
    def create_option_obj(self, ph):
        rules = ph.findall("rule")
        
        res_rules = []
        for e_rule in rules:
            res_rule = {}
            e_rule_par = e_rule.get("p")
            res_parameter = e_rule_par
            res_values = e_rule.text
            res_rule = dob.Rule(res_parameter, res_values)
            res_rules.append(res_rule)
                
        e_texts = ph.findall("text")
        if not e_texts:
            # FIXME: raise a warning
            return None
        if len(e_texts) > 1:
            # FIXME: raise a warning
            pass
        
        e_text = e_texts[0]
        res_text = self.create_token_obj(e_text)
        
        return dob.Option(res_rules, res_text)
    
    def create_formattedtext_obj(self, ph):
        tag = ph.tag
        try:
            t = self.FORMAT_TAGS[tag]
        except:
            t = "plain"
        if tag == "br":
            return dob.FormattedText(t)
        b_text = ph.text or ""
        children_text = []
        nodes = []
        for i, child in enumerate(ph.getchildren()):
            children_text.extend(["{{{0}}}".format(i), child.tail or ""])
            if child.tag == "placeholder":
                if child.get("t", "sub") == "sub":
                    obj = self.create_placeholder_obj(child)
                else:
                    obj = self.create_choice_obj(child)
            else:
                obj = self.create_formattedtext_obj(child)
            nodes.append(obj)
        text = b_text + "".join(children_text)
        return dob.FormattedText(t, self.clean(text), nodes)
    
    def create_choice_obj(self, ph):
        id_ = ph.get("id", "")
        if not id_:
            return None
        local_parameters = []
        lpars_tag = ph.get("p", "")
        if lpars_tag:
            local_parameters = lpars_tag.split(";")
        choice = self.choices[id_]
        opts = choice.findall("option")
        if not opts:
            # FIXME: raise warning
            return None
        options = []
        for opt in opts:
            option = self.create_option_obj(opt)
            options.append(option)
        return dob.Choice(options, self.dataframe, local_parameters)

    def innerxml(self, ph):
        pass

    def get_tree(self, df=None):
        return self.create_token_obj(self.main)
