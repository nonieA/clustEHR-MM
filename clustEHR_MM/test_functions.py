import json
import os
import pandas
import copy
from shutil import copytree
import re

from clustEHR_MM.module_edit_functions import get_edit_states,  transition_multiplier
from clustEHR_MM.synthea_functions import run_synthea, get_counts

def write_condition(attribute,logic,condition = None, ref_att = None):
    if logic == 'not_nil':
        if_dict = {
            "condition_type": "Attribute",
            "attribute": attribute,
            "operator": 'is not nil',
        }
    elif logic == 'equals':
        if_dict = {
            "condition_type": "Attribute",
            "attribute": attribute,
            "operator": '==',
            'value': True
        }
    elif logic == 'active_cond':
        if_dict = {
            "condition_type":"Active Condition"
        }
        if condition != None:
            if_dict["codes"] = [condition]
        if ref_att != None:
            if_dict['referenced_by_attribute'] = ref_att
    elif logic == 'active_care':
        if_dict = {
            "condition_type":"Active CarePlan",
            "codes":[condition]
        }
    elif logic == 'prior':
        if_dict = {
            "condition_type":"PriorState",
            "name": attribute
        }
    elif logic == 'obs':
        if_dict = {
            "condition_type":"Observation",
            "referenced_by_attribute": attribute,
            "operator": "is not nil"
        }
    else:
        if_dict = {
            "condition_type":"Attribute",
            "attribute":attribute,
            "operator": "==",
            "value": logic

        }

    return if_dict

def write_test_dict(dis_top_dict,mult,attribute,logic,condition = None, ref_att = None):
    new_top = {
            "Initial": {
      "type": "Initial",
      "direct_transition": "Delay_Until_Disease"
    },
    'test_disease':{
        'type': 'ConditionOnset',
        'codes': [{'system': 'SNOMED-CT',
        'code': 611700000,
        'display': 'Stomatitis'}],
        'direct_transition': "old_initial"
                    },
    "Delay_Until_Disease": {
      "type": "Delay",
      "range": {
        "low": 1,
        "high": 2,
        "unit": "years"
      },
      "direct_transition": "disease_based_transition"
    },

    "disease_based_transition":{
        "type": "Simple",
        "conditional_transition":[{
            "transition": 'test_disease',
        "condition": write_condition(attribute,logic,condition, ref_att)
        },
        {
        "transition": "Delay_Until_Disease"
        }]
    }
    }
    top_dict_copy = copy.deepcopy(dis_top_dict)
    end_states = get_edit_states(top_dict_copy)

    for i in end_states:
        edit_dict = top_dict_copy[i]
        transit_name = [i for i in edit_dict.keys() if 'transition' in i][0]
        if transit_name == 'complex_transition':
            for ind,val in enumerate(top_dict_copy[i][transit_name]):
                if 'distributions' in val.keys():
                    top_dict_copy[i][transit_name][ind]['distributions'] = transition_multiplier(val['distributions'],
                                                                                                 mult,
                                                                                                 list(top_dict_copy.keys()))
        else:
            top_dict_copy[i][transit_name] = transition_multiplier(top_dict_copy[i][transit_name],
                                                                   mult,
                                                                   list(top_dict_copy.keys()))

    top_dict_copy['old_initial'] = top_dict_copy.pop('Initial')
    if top_dict_copy['old_initial']['type'] == 'Initial':
        top_dict_copy['old_initial']['type'] = 'Simple'


    new_top.update(top_dict_copy)
    return new_top

def write_new_folder(disease_b,out_folder,mult,addition,attribute,logic,condition = None, ref_att = None):

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_top.json') as ft:
        top_dict = json.load(ft)

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_bottom.json') as fb:
        bottom_dict = json.load(fb)

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_framework.json') as fw:
        fw_dict = json.load(fw)

    new_disease = copy.deepcopy(fw_dict)
    new_top = write_test_dict(top_dict, mult,attribute,logic,condition, ref_att)

    new_disease['states'] = {**new_top,**bottom_dict}
    full_disease_out = out_folder + '/' + disease_b + '_' + addition

    if os.path.isdir(out_folder) == False:
        os.mkdir(out_folder)

    if os.path.isdir(full_disease_out) == False:
        current = 'modules/module_bases/' + disease_b
        new = full_disease_out
        copytree(current,new)

    disease_files = os.listdir(full_disease_out)

    delete_list = ['_top','_bottom','_framework']
    for i in disease_files:
        if any(j in i for j in delete_list):
            os.remove(full_disease_out + '/' + i)

    with open(full_disease_out + '/' + disease_b + '_' + addition+ '.json',"w") as out:
        json.dump(new_disease,out)

def test_attribute(attribute,logic,pop,disease_a,cond_dict,condition = None, ref_att = None):

    attribute2 = re.sub(' ','_',attribute)
    addition = attribute2 + '_' + re.sub(' ','_',logic)
    if condition != None:
        addition = addition + condition['code']
    if ref_att != None:
        addition = addition + re.sub(' ','_',ref_att)

    write_new_folder(
        'gout',
        'test/modules_name_test',
        2,
        addition,
        attribute,
        logic,
        condition,
        ref_att
    )
    run_synthea(
        'gout',
        'test/modules_name_test',
        pop,
        'test/csv_name_test/' + addition,
        4,
        addition
    )

    out = get_counts(disease_a,'Stomatitis','test/csv_name_test/' + addition,cond_dict)

    return out