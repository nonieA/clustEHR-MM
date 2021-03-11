import re
import json
import os
import copy
from shutil import copytree
with open('modules/module_bases/gout/gout_top.json') as f:
    gouttop = json.load(f)

with open('modules/module_bases/gout/gout_bottom.json') as h:
    goutbottom = json.load(h)

with open('modules/module_bases/copd/copd_top.json') as i:
    copdtop = json.load(i)

with open('modules/module_bases/copd/copd_bottom.json') as j:
    copdbottom = json.load(j)

with open('modules/module_bases/osteoporosis/osteoporosis_top.json') as k:
    osteoporosistop = json.load(k)

with open('modules/module_bases/osteoporosis/osteoporosis_bottom.json') as l:
    osteoporosisbottom = json.load(l)

with open('modules/module_bases/breast_cancer/breast_cancer_top.json') as m:
    breast_cancertop = json.load(m)

with open('modules/module_bases/breast_cancer/breast_cancer_bottom.json') as n:
    breast_cancerbottom = json.load(n)

def get_transitions(state_dict):
    transit_name = [i for i in state_dict.keys() if 'transition' in i][0]
    transit_dict = state_dict[transit_name]
    if transit_name == 'complex_transition':
        transit_keys = [[j['transition'] for j in i['distributions']] for i in transit_dict]
        transit_keys = [j for i in transit_keys for j in i]
        transit_keys = list(set(transit_keys))
    else:
        transit_keys = [i['transition'] for i in transit_dict]
    return transit_keys

def get_edit_states(top_dict):
    state_transitions = {k:get_transitions(v) for k,v in top_dict.items()}
    end_states = [k for k,v in state_transitions.items() if any(i not in state_transitions.keys() for i in v)]
    return end_states

def transition_multiplier(transit_dict,mult, states):
    transit_dict_new = transit_dict.copy()
    states = states + ['Terminal']
    dist = [i['distribution'] for i in transit_dict_new if i['transition'] not in states]
    if mult > 1/sum(dist):
        mult = 1/sum(dist)
    for i in transit_dict_new:
        x = i['distribution']
        if i['transition'] in states:
            i['distribution'] = 1 - 2* sum(dist)
        else:
            i['distribution'] = x * mult
    return transit_dict_new

def write_top_dict(dis_top_dict,disease,mult):
    new_top = {
        'Initial':{
            "type": "Delay",
            "distribution": {
                "kind": "EXACT",
                "parameters": {
                    "value": 1
                }
            },
            "unit": "years",
            "direct_transition": "disease_based_transition",
            "name": "Initial"
        },
        "disease_based_transition":{
            "type": "Simple",
            "conditional_transition":[{
                "transition": 'old_initial',
            "condition": {
                "condition_type": "Attribute",
                "attribute": disease,
                "operator": "==",
                "value": "true"
            }
        },
            {
            "transition": "Initial"
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

def write_new_folder(disease_a,disease_b,out_folder,mult):

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_top.json') as ft:
        top_dict = json.load(ft)

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_bottom.json') as fb:
        bottom_dict = json.load(fb)

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_framework.json') as fw:
        fw_dict = json.load(fw)

    new_disease = copy.deepcopy(fw_dict)
    new_top = write_top_dict(top_dict,disease_a,mult)
    new_disease['states'] = {**new_top,**bottom_dict}
    full_disease_out = 'clustEHR-MM/' + out_folder + '/' + disease_b

    if os.path.isdir('clustEHR-MM/' + out_folder) == False:
        os.mkdir('clustEHR-MM/' + out_folder)

    if os.path.isdir(full_disease_out) == False:
        current = 'modules/module_bases/disease_b'
        new = 'clustEHR-MM/' + out_folder + '/' + disease_b
        copytree(current,new)

    disease_files = os.listdir(full_disease_out)

    delete_list = ['_top','_bottom','_framework']
    for i in disease_files:
        if any(j in i for j in delete_list):
            os.remove(full_disease_out + '/' + i)

    with open(full_disease_out + '/' + disease_b + '.json') as out:
        json.dump(new_disease)




