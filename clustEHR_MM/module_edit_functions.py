import json
import os
import copy
from shutil import copytree

def complex_condition_trans(transit_dict):
    if 'transition' in transit_dict.keys():
        return [transit_dict['transition']]
    else:
        return [i['transition'] for i in transit_dict['distributions']]

def get_transitions(state_dict):
    transit_name = [i for i in state_dict.keys() if 'transition' in i][0]
    transit_dict = state_dict[transit_name]
    if transit_name == 'complex_transition':
        transit_keys = [complex_condition_trans(i) for i in transit_dict]
        transit_keys = [j for i in transit_keys for j in i]
        transit_keys = list(set(transit_keys))
    elif isinstance(transit_dict,str):
        transit_keys = transit_dict
    else:
        transit_keys = [i['transition'] for i in transit_dict]
    if type(transit_keys) != list:
        transit_keys = [transit_keys]

    return transit_keys

def get_edit_states(top_dict):
    state_transitions = {k:get_transitions(v) for k,v in top_dict.items()}
    end_states = [k for k,v in state_transitions.items() if any(i not in state_transitions.keys() for i in v)]
    return end_states

def transition_multiplier(transit_dict,mult, states):
    transit_dict_new = transit_dict.copy()
    states = states + ['Terminal']

    dist = [i['distribution'] for i in transit_dict_new if i['transition'] not in states]
    if isinstance(dist[0],dict):
        dist2 = [j for i in dist for j in i.values() if isinstance(j,float)]
        if mult > 1/sum(dist2):
            mult = 1/sum(dist2)
        num_key = [k for k,v in dist[0].items() if isinstance(v,float)][0]
        for i in transit_dict_new:
            x = i['distribution'][num_key]
            if i['transition'] in states:
                i['distribution'][num_key] = 1 - mult * sum(dist2)
            else:
                i['distribution'][num_key] = x * mult
    else:
        if mult > 1/sum(dist):
            mult = 1/sum(dist)
        for i in transit_dict_new:
            x = i['distribution']
            if i['transition'] in states:
                i['distribution'] = 1 - mult * sum(dist)
            else:
                i['distribution'] = x * mult
    return transit_dict_new

def rename_transitions(state_dict,states_list):
    state_dict2 = copy.deepcopy(state_dict)
    transit_name = [i for i in state_dict2.keys() if 'transition' in i][0]
    if transit_name == 'complex_transition':
        for i in state_dict2[transit_name]:
            if 'distributions' in i.keys():
                for j in i['distributions']:
                    if j['transition'] in states_list:
                        j['transition'] = j['transition'] + '_new'
            else:
                if i['transition'] in states_list:
                    i['transition'] = i['transition'] + '_new'
    elif (isinstance(state_dict2[transit_name],str)) and (state_dict2[transit_name] in states_list):
        state_dict2[transit_name] = state_dict2[transit_name] + '_new'
    else:
        for i in state_dict2[transit_name]:
            if i['transition'] in states_list:
                i['transition'] = i['transition'] + '_new'
    return state_dict2

def rename_transitions_terminal(state_dict):
    state_dict2 = copy.deepcopy(state_dict)
    transit_name = [i for i in state_dict2.keys() if 'transition' in i][0]
    if transit_name == 'complex_transition':
        for i in state_dict2[transit_name]:
            if 'distributions' in i.keys():
                for j in i['distributions']:
                    if j['transition'] == 'Terminal':
                        j['transition'] = 'Delay_Until_Disease'
                    if j['transition'] == 'Initial':
                        j['transition'] = 'Initial_old'
            else:
                if i['transition'] == 'Terminal':
                    i['transition'] = 'Delay_Until_Disease'
                if i['transition'] == 'Initial':
                    i['transition'] = 'Initial_old'
    elif isinstance(state_dict2[transit_name],str):
        if state_dict2[transit_name] == 'Terminal':
            state_dict2[transit_name] = 'Delay_Until_Disease'
        if state_dict2[transit_name] == 'Initial':
            state_dict2[transit_name] = 'Initial_old'
    else:
        for i in state_dict2[transit_name]:
            if i['transition'] == 'Terminal':
                i['transition'] = 'Delay_Until_Disease'
            if i['transition'] == 'Initial':
                i['transition'] = 'Initial_old'
    return state_dict2

def rename_states(top_dict,old = True):
    if old:
        new_dict = {k + '_old' if k == 'Initial' else k: rename_transitions_terminal(v) for k,v in top_dict.items()}
    else:
        new_dict = {k + '_new':rename_transitions(v,top_dict.keys()) for k,v in top_dict.items()}
    return new_dict

def write_conditional(disease):
    disease_cond = {
        'appendicitis':['appendicitis','equals'],
        'allergic_rhinitis':['allergic_rhinitis','not_nil'],
        'asthma':['asthma_careplan','not_nil'],
        'attention_deficit_disorder':['adhd','not_nil'],
        'breast_cancer':['breast_cancer_condition','not_nil'],
        'bronchitis':['bronchitis_careplan','not_nil'],
        'cerebral_palsy':['Anterior_Drooling','not_nil'],
        'colorectal_cancer':{
            "condition_type": "Or",
            "conditions": [
              {
                "condition_type": "Attribute",
                "attribute": "colorectal_adenoma",
                "operator": "is not nil"
              },
              {
                "condition_type": "Attribute",
                "attribute": "colorectal_cancer_stage",
                "operator": "is not nil"
              }
            ]
          },
        'congestive_heart_failure':['chf','not nil'],
        'copd':['copd variant','not_nil'],
        'cystic_fibrosis':['Cystic_Fibrosis','not_nil'],
        'dementia':['Type of Alzheimer\'s','not_nil'],
        'dermatitis':['not_atopic','nil'],
        'Diabetes':['diabetes','equals'],
        'diabetes': ['diabetes', 'equals'],
        'ear_infections':['Otitis_Media','equals'],
        'epilepsy':['seizure','not_nil'],
        'fibromyalgia':['fibromyalgia_careplan','not_nil'],
        'gallstones':['Cholelithiasis','equals'],
        'gout':['gout_nsaid','not_nil'],
        'hypothyroidism':['hypothyroidism','not_nil'],
        'lung_cancer':['Lung Cancer','not_nil'],
        'sore_throat':['Sore Throat Condition','not_nil'],
        'rheumatoid_arthritis':['ra_careplan','not_nil'],
        'urinary_tract_infections':['uti','not_nil']
    }

    if isinstance(disease_cond[disease],dict):
        if_dict = disease_cond[disease]
    elif disease_cond[disease][1] == 'not_nil':
        if_dict = {
            "condition_type": "Attribute",
            "attribute": disease_cond[disease][0],
            "operator": 'is not nil',
        }
    elif disease_cond[disease][1] == 'equals':
        if_dict = {
            "condition_type": "Attribute",
            "attribute": disease_cond[disease][0],
            "operator": '==',
            'value':True
            }
    else:
        if_dict = {
            "condition_type": "Attribute",
            "attribute": disease_cond[disease][0],
            "operator": 'is nil',
        }
    return if_dict

def write_and_condition(diseases):
    if_dict = {
        "condition_type":"And",
        "conditions":[write_conditional(i) for i in diseases]
    }

def delay_state(time,units):
    if isinstance(time,list):
        state = {
            "type":"Delay",
            "range": {
                "low": min(time),
                "high":max(time),
                'units':units
            },
            "direct_transition":'Initial_new'
        }
    else:
        state = {
            "type":"Delay",
            "exact":{
                "quantity":time,
                "units":units
            },
            "direct_transition":'Initial_new'
        }
    return state


def write_top_dict(dis_top_dict,disease,mult, time_delay = None,units = None):
    if time_delay == None:
        end_transition = 'Initial_new'
    else:
        end_transition = 'time_delay'

    if isinstance(disease,list):
        condition_dict = write_and_condition(disease)
    else:
        condition_dict = write_conditional(disease)

    new_top = {
            "Initial": {
      "type": "Initial",
      "direct_transition": "disease_based_transition"
    },

    "Delay_Until_Disease": {
      "type": "Delay",
      "range": {
        "low": 1,
        "high": 2,
        "unit": "weeks"
      },
      "direct_transition": "disease_based_transition2"
    },

    "disease_based_transition":{
        "type": "Simple",
        "conditional_transition":[{
            "transition": end_transition,
        "condition": condition_dict
        },
        {
        "transition": "Initial_old"
        }]
    },
        "disease_based_transition2": {
            "type": "Simple",
            "conditional_transition": [{
                 "transition": end_transition,
                "condition": condition_dict
            },
                {
                    "transition": "Delay_Until_Disease"
                }]
        }
    }

    if time_delay != None:
        new_top['time_delay'] = delay_state(time_delay,units)

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

    disease_top = rename_states(top_dict_copy, old = False)
    old_top = rename_states(copy.deepcopy(dis_top_dict))

    if 'Potential_COPD_Nonsmoker' in old_top.keys():
        for i in old_top['Potential_COPD_Nonsmoker']['complex_transition'][1]['distributions']:
            if i['transition'] == 'Potential_COPD_Nonsmoker':
                i['transition'] = 'disease_based_transition2'
        for i in old_top['Potential_COPD_Smoker']['complex_transition']:
            for j in i['distributions']:
                if j['transition'] == 'Potential_COPD_Nonsmoker':
                    j['transition'] = 'disease_based_transition2'

    if disease_top['Initial_new']['type'] == 'Initial':
        disease_top['Initial_new']['type'] = 'Simple'

    if old_top['Initial_old']['type'] == 'Initial':
        old_top['Initial_old']['type'] = 'Simple'


    new_top.update(disease_top)
    new_top.update(old_top)
    return new_top

def write_test_dict(dis_top_dict,disease,mult):

    if isinstance(disease,list):
        condition_dict = write_and_condition(disease)
    else:
        condition_dict = write_conditional(disease)

    new_top = {
            "Initial": {
      "type": "Initial",
      "direct_transition": "disease_based_transition"
    },

    "Delay_Until_Disease": {
      "type": "Delay",
      "range": {
        "low": 1,
        "high": 2,
        "unit": "weeks"
      },
      "direct_transition": "disease_based_transition2"
    },
    'test_disease':{
        'type': 'ConditionOnset',
        'codes': [{'system': 'SNOMED-CT',
        'code': 611700000,
        'display': 'Stomatitis'}],
        'direct_transition': "Initial_new"
                    },

    "disease_based_transition":{
        "type": "Simple",
        "conditional_transition":[{
            "transition": 'test_disease',
        "condition": condition_dict
        },
        {
        "transition": "Initial_old"
        }]
    },
        "disease_based_transition2": {
            "type": "Simple",
            "conditional_transition": [{
                 "transition": 'test_disease',
                "condition": condition_dict
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

    disease_top = rename_states(top_dict_copy, old = False)
    old_top = rename_states(copy.deepcopy(dis_top_dict))

    if 'Potential_COPD_Nonsmoker' in old_top.keys():
        for i in old_top['Potential_COPD_Nonsmoker']['complex_transition'][1]['distributions']:
            if i['transition'] == 'Potential_COPD_Nonsmoker':
                i['transition'] = 'disease_based_transition2'
        for i in old_top['Potential_COPD_Smoker']['complex_transition']:
            for j in i['distributions']:
                if j['transition'] == 'Potential_COPD_Nonsmoker':
                    j['transition'] = 'disease_based_transition2'

    if disease_top['Initial_new']['type'] == 'Initial':
        disease_top['Initial_new']['type'] = 'Simple'

    if old_top['Initial_old']['type'] == 'Initial':
        old_top['Initial_old']['type'] = 'Simple'


    new_top.update(disease_top)
    new_top.update(old_top)
    return new_top

def write_new_folder(disease_a,disease_b,out_folder,mult,test = False):

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_top.json') as ft:
        top_dict = json.load(ft)

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_bottom.json') as fb:
        bottom_dict = json.load(fb)

    with open('modules/module_bases/' + disease_b + '/' + disease_b + '_framework.json') as fw:
        fw_dict = json.load(fw)

    new_disease = copy.deepcopy(fw_dict)
    if test:
        new_top = write_test_dict(top_dict, disease_a, mult)
    else:
        new_top = write_top_dict(top_dict,disease_a,mult)
    new_disease['states'] = {**new_top,**bottom_dict}


    with open(out_folder + '/' + disease_b + '.json',"w") as out:
        json.dump(new_disease,out)


if __name__ == '__main__':

    with open('modules/module_bases/copd/copd_top.json') as fb:
        copd_top = json.load(fb)


    with open('modules/module_bases/osteoporosis/osteoporosis_top.json') as fl:
        osteoporosis_top = json.load(fl)


    with open('test/test2/appendicitis_new_test/appendicitis_new_test.json') as fl:
        app = json.load(fl)
    write_new_folder('diabetes', 'gout', 'test9', 2, 'test')

    modules = os.listdir('modules/module_bases')
    [write_new_folder(i,'gout','test/test2/modules',2,addition = 'disease_a_test' + i,test =True) for i in modules]