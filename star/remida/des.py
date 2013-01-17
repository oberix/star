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

import os
import sys
import re
import decimal as dc
import des_filters as df 
from xml.etree.ElementTree import XML, fromstring, tostring

BASEPATH = os.path.abspath(os.path.join(
        os.path.dirname(sys.argv[0]),
        os.path.pardir))
sys.path.append(BASEPATH)
sys.path = list(set(sys.path))


################
# gerarchia tags
tags = {"paragraph": ["placeholder", "choice",], "choice": ["option",], 
        "option": ["parameter", "text",], "text": ["placeholder", "choice",]}


#############################################
# regex per i tag di creazione dinamica testo
pattern_paragraph_tag = r"""
    <\s*paragraph=([^>]*)>(.*?)<\s*/\s*paragraph\s*>
"""
pattern_paragraph_tag = re.compile(pattern_paragraph_tag, re.IGNORECASE | re.VERBOSE | 
                               re.MULTILINE | re.DOTALL | re.UNICODE)   

pattern_choice_tag = r"""
    <\s*choice=([^>]*)>(.*?)<\s*/\s*choice\s*>
"""
pattern_choice_tag = re.compile(pattern_choice_tag, re.IGNORECASE | re.VERBOSE | 
                            re.MULTILINE | re.DOTALL | re.UNICODE)   

pattern_option_tag = r"""
    <\s*option\s*>(.*?)<\s*/\s*option\s*>
"""
pattern_option_tag = re.compile(pattern_option_tag, re.IGNORECASE | re.VERBOSE | 
                            re.MULTILINE | re.DOTALL | re.UNICODE)   

pattern_parameter_tag = r"""
    <\s*parameter=([^>]*)>(.*?)<\s*/\s*parameter\s*>
"""
pattern_parameter_tag = re.compile(pattern_parameter_tag, re.IGNORECASE | re.VERBOSE | 
                           re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_text_tag = r"""
    <\s*text\s*>(.*?)<\s*/\s*text\s*>
"""
pattern_text_tag = re.compile(pattern_text_tag, re.IGNORECASE | re.VERBOSE | 
                          re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_placeholder_tag = r"""
    <\s*(placeholder|choice)=([^/>]*)/>
"""
pattern_placeholder_tag = re.compile(pattern_placeholder_tag, re.IGNORECASE | re.VERBOSE | 
                                 re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_parameter = r"""
    parameter=("[^"]+")|parameter=('[^']+')|parameter=({[0-9]+})
"""
pattern_parameter = re.compile(pattern_parameter, re.IGNORECASE | re.VERBOSE | 
                               re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_filters = r"""
    filters=((?:(?:"[^\"]+"|'[^']+'|[^\s"'(\>)>]+)\|?)*)
"""
pattern_filters = re.compile(pattern_filters, re.IGNORECASE | re.VERBOSE | 
                             re.MULTILINE | re.DOTALL | re.UNICODE)


########################################
# regex per i tag di formattazione testo            
pattern_bold = r"""
    <\s*b\s*>(.*?)<\s*/\s*b\s*>
"""
pattern_bold = re.compile(pattern_bold, re.IGNORECASE | re.VERBOSE | 
                          re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_italic = r"""
    <\s*i\s*>(.*?)<\s*/\s*i\s*>
"""
pattern_italic = re.compile(pattern_italic, re.IGNORECASE | re.VERBOSE | 
                            re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_underline = r"""
    <\s*u\s*>(.*?)<\s*/\s*u\s*>
"""
pattern_underline = re.compile(pattern_underline, re.IGNORECASE | re.VERBOSE | 
                               re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_sub = r"""
    <\s*sub\s*>(.*?)<\s*/\s*sub\s*>
"""
pattern_sub = re.compile(pattern_sub, re.IGNORECASE | re.VERBOSE | 
                         re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_sup = r"""
    <\s*sup\s*>(.*?)<\s*/\s*sup\s*>
"""
pattern_sup = re.compile(pattern_sup, re.IGNORECASE | re.VERBOSE | 
                         re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_newline = r"""
    <\s*br\s*/>
"""
pattern_newline = re.compile(pattern_newline, re.IGNORECASE | re.VERBOSE | 
                             re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_title = r"""
    <\s*title\s*>(.*?)<\s*/\s*title\s*>
"""
pattern_title = re.compile(pattern_title, re.IGNORECASE | re.VERBOSE | 
                           re.MULTILINE | re.DOTALL | re.UNICODE)

pattern_uppercase = r"""
    <\s*upper\s*>(.*?)<\s*/\s*upper\s*>
"""
pattern_uppercase = re.compile(pattern_uppercase, re.IGNORECASE | re.VERBOSE | 
                               re.MULTILINE | re.DOTALL | re.UNICODE)

    
TEX_ESCAPE = [
    (re.compile("€"), "\\officialeuro"), 
    (re.compile("%"), "\\%"), 
    (re.compile("&"), "\\&"),
    (re.compile("\$(?!\w+)"), "\\$"),
    (re.compile(">=(?!\{)"), r"$\\ge$"),
    (re.compile("<=(?!\{)"), r"$\\le$"),
    (re.compile(">(?!\{)"), r"$>$"),
    (re.compile("<(?!\{)"), r"$<$"),
    (re.compile("\n"), "\\\\"),
    (re.compile("_"), "\_"),
    (re.compile("/"), "/\-"), 
    (re.compile("\^"), "\textasciicircum"),
    (re.compile("~"), "\normaltilde"),
    ]


# TODO: fill this up
HTML_ESCAPE = [
    (re.compile("€"), "EURO"),
    ]


# TODO: move this to template.py
def escape(string, patterns=None):
    ''' Escape string to work with LaTeX.
    The function calls TEX_ESCAPE dictionary to match regexp with their escaped
    version.

    @ param string: the string to escape
    @ param patterns: a pattern/string mapping dictionary
    @ return: escaped version of string

    '''
    if patterns is None:
        patterns = TEX_ESCAPE
    for pattern, sub in patterns:
        string = re.sub(pattern, sub, string)
    return string


class Des(object):
    '''
    classe per l'oggetto testo automatico
    '''
    def __init__(self, data):
        if type(data.main) is unicode:
            self.main = fromstring(data.main.encode("utf8"))
        else:
            self.main = fromstring(data.main)
        
#        if type(data.portfolio) is unicode:
#            self.main = fromstring(data.portfolio.encode("utf8"))
#        else:
#            self.main = fromstring(data.portfolio)
        self.phchoices = self.parse_choice_placeholders()
        dom = XML(data.main)
        print(dom)
        print(self.phchoices)
        print(dom.text)
        print(dom.tail)
        print("".join([tostring(e) for e in dom]))
        
#        self.placeholders = self.parse_placeholders()
#        self.choices = self.parse_choices()
#        self.test_parameters = data.df.rename(columns=data.lm)
#        self.paragraphs = self.find_paragraphs(self.main)

    def clean(self, string):
        # togliamo gli spazi vuoti e le newline iniziali e finali
        string = string.strip().strip("\n")
        # dividiamo in righe
        lines = string.splitlines()
        for i in xrange(len(lines)):
            lines[i] = unicode(" ", "utf8").join(lines[i].split())
        return unicode(" ", "utf8").join(lines)
         
    def find_paragraphs(self, string):
        res = []
        ms = pattern_paragraph_tag.finditer(string)
        if ms:
            for m in ms:
                id_ = m.groups()[0].strip()
                res.append({"start": m.start(), "end": m.end(), 
                            "id": id_,
                            "value": self.clean(m.groups()[1])})
        return res
                
    def find_choices(self, string):
        res = []
        ms = pattern_choice_tag.finditer(string)
        if ms:
            for m in ms:
                id_ = m.groups()[0].strip()[1:-1]
                res.append({"start": m.start(), "end": m.end(), 
                            "id": id_, 
                            "value": m.groups()[1]})
        return res

    def find_options(self, string):
        res = []
        ms = pattern_option_tag.finditer(string)
        if ms:
            for m in ms:
                res.append({"start": m.start(), "end": m.end(),  
                            "value": m.groups()[0]})
        return res
        
    def find_parameters(self, string):
        res = []
        ms = pattern_parameter_tag.finditer(string)
        if ms:
            for m in ms:
                id_ = m.groups()[0].strip()                 
                res.append({"start": m.start(), "end": m.end(), 
                            "id": id_,
                            "value": m.groups()[1]})
        return res
        
    def find_texts(self, string):
        res = []
        ms = pattern_text_tag.finditer(string)
        if ms:
            for m in ms:
                res.append({"start": m.start(), "end": m.end(),  
                            "value": self.clean(m.groups()[0])})
        return res
    
    def find_placeholders(self, string):
        res = []
        ms = pattern_placeholder_tag.finditer(string)
        if ms:
            for m in ms:
                t = m.groups()[0] 
                id_ = m.groups()[1].strip()                            
                res.append({"start": m.start(), "end": m.end(), 
                            "type": t,
                            "id": id_,})
        return res

    def parse_choice_placeholders(self):
        phchoices = {}
        
        phs = self.main.findall("placeholder")
#        phs.extend(self.portfolio("placeholder"))
        for ph in phs:
            attrib = ph.attrib
            if "t" in attrib and attrib["t"] == "choice":
                k = attrib.get("id", "")
                tag_p = attrib.get("p", "")
                parameters = []
                ps = tag_p.split(";")
                for p in ps:
                    p_splt = p.split("|")
                    parameter = p_splt[0]
                    filters = p_splt[1:]
                    parameters.append((parameter, filters))
                if k:
                    phchoices[k] = {"element": ph, "parameters": parameters,}                
        
        return phchoices
    
    def parse_rules_values(self, string_in):
        pass
        
    
#    def parse_choices(self):
#        cs = self.portfolio.findall("choices")
#        
#        for c in cs:
#            k = c.attrib.get("id", "")
#            opts = c.findall("option")
#            for opt in opts:
#                rs = c.findall("rule")
#                rules = []
#                for r in rs:
#                    tag_p = r.attrib.get("p", "").split("|")
#                    parameter = tag_p[0]
#                    filters = tag_p[1:]
#                    rules_text = r.text
                
    
    def parse_paragraph(self):
        pass
                         
    def get_par_filters(self, k):
        l = k.split("|")
        par = l[0]
        
        if (par.startswith("\"") and par.endswith("\"") or
            par.startswith("'") and par.endswith("'")):
            par = self.test_parameters[par[1:-1]][0]

        filters = l[1:]        
        return par, filters
    
    def filter_data(self, data, filters):
        res = data
        for f in filters:
            if ((f.startswith("\"") and f.endswith("\""))
                or (f.startswith("'") and f.endswith("'"))):
                try:
                    res = res[f[1:-1]]
                except:
                    res = ""
            else:
                l = f.split(":")
                filter_name = l[0]
                if len(l) > 1:
                    args = l[1].split(",")
                else:
                    args = []
                try:
                    des_filter = getattr(df, filter_name)
                    res = des_filter(res, *args)
                except:
                    res = ""
        return res
    
#    def parse_placeholders(self):
#        placeholders = self.find_placeholders(self.main)
#        placeholders.extend(self.find_placeholders(self.portfolio))
#        
#        res = {}
#        
#        for ph in placeholders:
#            l = ph["id"].split("parameter=")
#            k = l[0].strip()
#            parameters_local = []
#            parameters_local.extend([p.strip() for p in l[1:]])
#            res[k] = {"type": ph["type"], "start": ph["start"], "end": ph["end"], 
#                      "parameters_local": parameters_local}
#    
#        print(res)
#        return res
                           
    def parse_choices(self):
        choices = self.portfolio.findall("choice")
        result = {}
        
        for choice in choices:
            k = choice["id"]
            options = self.find_options(choice["value"])
            for option in options:
                v = {"text": "", "parameters": []}
                text = self.find_texts(option["value"])[0]
                v["text"] = text["value"]
                
                parameters = self.find_parameters(option["value"])
                for parameter in parameters:
                    parameter_id = parameter["id"]
                    # FIXME: decommentare appena ho capito come gestire i parametri
                    # locali
                        
                    parameter_values = parameter["value"].split(",")
                    if len(parameter_values)==2:
                        # eliminiamo le parentesi
                        parameter_values = [[parameter_values[0][1:],
                                             0 if parameter_values[0][0] == "[" 
                                             else 1],
                                            [parameter_values[1][:-1],
                                             0 if parameter_values[1][-1] == "]" 
                                             else 1]]
                        if parameter_values[0][0] == "inf":
                            parameter_values[0][0] = -sys.maxint - 1
                        parameter_values[0][0] = unicode(str(parameter_values[0][0]), 
                                                         "utf8")
                        if parameter_values[1][0] == "inf":
                            parameter_values[1][0] = sys.maxint
                        parameter_values[1][0] = unicode(str(parameter_values[1][0]), 
                                                         "utf8")
                    else:
                        if parameter_values[0] == "inf":
                            parameter_values[0] = sys.maxint
                        parameter_values[0] = unicode(str(parameter_values[0]), 
                                                      "utf8")
                    v["parameters"].append((parameter_id, tuple(parameter_values)))
                try:
                    result[k].append(v)
                except:
                    result[k] = [v]
        print("\n\n")
        print(self.choices)
        return result

    def check_parameters(self, option_parameters): 
        for e in option_parameters:
            par = e[0]
            values = e[1]
            
            l = par.split("|")
            par = l[0]
            if (par.startswith("\"") and par.endswith("\"") or
                par.startswith("'") and par.endswith("'")):
                par = par[1:-1]
            else:
                continue
            if not par in self.test_parameters:
                continue
            filters = l[1:]
            test_value = self.test_parameters[par][0]
            test_value = self.filter_data(test_value, filters)
            
            if len(values) == 2:
                values_min_id = values[0][0]
                values_min_par, values_min_filters = self.get_par_filters(values_min_id)
                values_min = self.filter_data(values_min_par, values_min_filters)

                values_max_id = values[1][0]
                values_max_par, values_max_filters = self.get_par_filters(values_max_id)
                values_max = self.filter_data(values_max_par, values_max_filters)
                
#                values_min_l = values_min.split("|")
#                values_min = values_min_l[0]
#                if (values_min.startswith("\"") and values_min.endswith("\"") or
#                    values_min.startswith("'") and values_min.endswith("'")):
#                    values_min = self.test_parameters[values_min[1:-1]][0]
#                values_min_filters = values_min_l[1:]
#                values_min = self.filter_data(values_min, values_min_filters)
#                
#                values_max = values[1][0]
#                values_max_l = values_max.split("|")
#                values_max = values_max_l[0]
#                if (values_max.startswith("\"") and values_min.endswith("\"") or
#                    values_max.startswith("'") and values_min.endswith("'")):
#                    values_max = self.test_parameters[values_max[1:-1]][0]
#                values_max_filters = values_max_l[1:]
#                values_max = self.filter_data(values_max, values_max_filters)
                
                try:
                    values_min = dc.Decimal(str(values_min))
                    values_max = dc.Decimal(str(values_max))
                    test_value = dc.Decimal(str(test_value))
                except:
                    values_min = str(values_min)
                    values_max = str(values_max)
                    test_value = str(test_value)
                limits = (values[0][1], values[1][1])
                
                if limits == (0,0) and values_min <= test_value <= values_max:
                    return True
                elif limits == (1,0) and values_min < test_value <= values_max:
                    return True
                elif limits == (0,1) and values_min <= test_value < values_max:
                    return True
                elif limits == (1,1) and values_min < test_value < values_max:
                    return True
            elif len(values) == 1:
                value_l = values[0].split("|")
                value = value_l[0]
                if (value.startswith("\"") and value.endswith("\"") or
                    value.startswith("'") and value.endswith("'")):
                    value = self.test_parameters[value[1:-1]][0]
                value_filters = value_l[1:]
                value = self.filter_data(value, value_filters)
                
                try:
                    value = dc.Decimal(str(value))
                    test_value = dc.Decimal(str(test_value))
                except:
                    value = str(value)
                    test_value = str(test_value)
                if value == test_value:
                    return True
        return False
                            
    def select_choice(self, choice_id):
        options = self.choices[choice_id]
        for option in options:
            option_parameters = option["parameters"]
            if self.check_parameters(option_parameters):
                return option["text"]
        return ""
            
    def substitute_placeholders(self, string_in):
#        placeholders = self.find_placeholders(string_in)
        list_out = []
        offset = 0
        for ph_id in self.placeholders:
            t = self.placeholders[ph_id]["type"]
            s = self.placeholders[ph_id]["start"]
            e = self.placeholders[ph_id]["end"]
            list_out.append(string_in[offset: s])
            offset = e
            if t == "placeholder":
                par, filters = self.get_par_filters(ph_id)
                v = self.test_parameters[par][0]
                v = self.filter_data(v, filters)              
                if type(v) is list or type(v) is list:
                    v = unicode(", ", "utf8").join([unicode(str(e), "utf8") 
                                                    for e in v])
                elif type(v) is dict:
                    v = unicode(", ", "utf8").join([unicode(str(e), "utf8") 
                                                    for e in v.values()])
                if not type(v) is unicode:
                    v = str(v).decode("utf8")
                list_out.append(v)
            elif t == "choice":
                choice_id = ph_id[1:-1]
                text = self.select_choice(choice_id)
                list_out.append(self.substitute_placeholders(text))
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out

    def format_text(self, text):
        return text
        
    def elab_text(self, text):
        text = self.substitute_placeholders(text)
        text = self.format_text(text)
        text = escape(text)
        text = unicode("{0}", "utf8").format(text)
        return text  
    
    def out(self):
        raise NotImplementedError
    

class TexDes(Des):
    def __init__(self, data):
        Des.__init__(self, data)

    def set_bold(self, string_in):
        ms = pattern_bold.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("\\textbf{{{0}}}", "utf8").format(m.groups()[0]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out
            
    def set_italic(self, string_in):
        ms = pattern_italic.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("\\textit{{{0}}}", "utf8").format(m.groups()[0]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out

    def set_underline(self, string_in):
        ms = pattern_underline.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("\\underline{{{0}}}", "utf8").format(m.groups()[0]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out
        
    def set_textsuperscript(self, string_in):
        ms = pattern_sup.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("$^{{{0}}}$", "utf8").format(m.groups()[0]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out

    def set_textsubscript(self, string_in):
        ms = pattern_sub.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("$_{{{0}}}$", "utf8").format(m.groups()[0]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out

    def set_newline(self, string_in):
        ms = pattern_newline.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("\\newline ", "utf8"))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out
    
    def set_title(self, string_in):
        ms = pattern_title.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                s = m.groups()[0]
                list_out.append(unicode("{0}", "utf8").format(s[0].upper() + s[1:]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out        
    
    def set_upper(self, string_in):
        ms = pattern_title.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                list_out.append(unicode("{0}", "utf8").format(m.groups()[0].upper()))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out          
    
    def format_text(self, string_in):
        string_out = string_in
        string_out = self.set_bold(string_out)
        string_out = self.set_italic(string_out)
        string_out = self.set_textsubscript(string_out)
        string_out = self.set_textsuperscript(string_out)
        string_out = self.set_underline(string_out)
        string_out = self.set_newline(string_out)
        string_out = self.set_title(string_out)
        string_out = self.set_upper(string_out)
        return string_out
        
    def out(self):
        res = []
        for paragraph in self.paragraphs:
            paragraph_text = self.elab_text(paragraph["value"])
            res.append(unicode("{{{0}}}", "utf8").format(paragraph_text))
        return unicode("", "utf8").join(res)

        
class HTMLDes(Des):
    def __init__(self, data):
        Des.__init__(self, data)
    
    def set_title(self, string_in):
        ms = pattern_title.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                s = m.groups()[0]
                list_out.append(unicode("<font style='text-transform: capitalize;'>{0}</font>", 
                                        "utf8").format(s[0].upper() + s[1:]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out           
    
    def set_uppercase(self, string_in):
        ms = pattern_title.finditer(string_in)
        
        offset = 0
        list_out = []
        if ms:
            for m in ms:
                list_out.append(string_in[offset:m.start()])
                s = m.groups()[0]
                list_out.append(unicode("<font style='text-transform: uppercase;'>{0}</font>", 
                                        "utf8").format(s[0].upper() + s[1:]))
                offset = m.end()
        
        list_out.append(string_in[offset:])
        string_out = unicode("", "utf8").join(list_out)
        return string_out             
    
    def out(self):
        res = []
        for paragraph in self.paragraphs:
            paragraph_id = paragraph["id"]
            paragraph_text = self.elab_text(paragraph["value"])
            res.append(unicode("<div id='{0}' class='paragraph'>", 
                               "utf8").format(paragraph_id))
            res.append(paragraph_text)
            res.append(unicode("</div>", "utf8"))
        return unicode("", "utf8").join(res)


def main():
    import pandas as pnd
    import share.bag
    
    try:
        b1 = share.bag.Bag.load("/home/studiabo/SchedaPaese/SchedaPaeseRep/E1/ITA/tabmixA11.pickle")
        lista_pos = [{"nome": des, "saldo": sc,} 
                 for des, sc in list(b1.df[["DES", "SC"]].to_records(False))[:-1]]
        print("prima lista:\n{0}\n\n".format(lista_pos))
    except:
        lista_pos = []
    try:
        b2 = share.bag.Bag.load("/home/studiabo/SchedaPaese/SchedaPaeseRep/E1/ITA/tabmixA12.pickle")
        lista_neg = [{"nome": des, "saldo": sc,} 
                 for des, sc in list(b2.df[["DES", "SC"]].to_records(False))[:-1]]
        print("seconda lista:\n{0}\n\n".format(lista_neg))        
    except:
        lista_neg = []

    df = pnd.DataFrame([[lista_pos, lista_neg]], 
                       columns=["lista_pos", "lista_neg"])
    lm = {"lista_pos": "lista categorie positive",
          "lista_neg": "lista categorie negative",}
#    lista1 = ["aaa", "bbb", "ccc", {"nome": "ddd", "valore": 5}]
#    lista2 = ["111", "222"]
#    lista3 = {1:1,2:2,3:1,4:2,5:1,6:2}
#    df = pnd.DataFrame([[lista1, lista2, lista3, 2.795236127]], 
#                       columns=["col1", "col2", "col3", "col4"])
#    lm = {"col1": "prima lista", "col2": "seconda lista", 
#          "col3": "terza lista", "col4": "delta di prova"}
#    lm = {"lista_pos": "prima lista",
#          "lista_neg": "seconda lista",}
    cod = ""
    
    b = share.bag.Bag(df, cod=cod, stype="text", lm=lm)
    with open(os.path.join("./test_main.des"), "rb") as fd:
        main_file =  fd.read()
    
    with open(os.path.join("/home/lcurzi/testi_auto/portfolio_schedapaese.des"), "rb") as fd:
        portfolio_file =  fd.read()
        
    b.main = main_file
    b.portfolio = portfolio_file
    
    td = TexDes(b)
    o = td.out()
    print(o)
    
#    hd = HTMLDes(b)
#    print(hd.out())

    
if __name__ == '__main__':
    main()
