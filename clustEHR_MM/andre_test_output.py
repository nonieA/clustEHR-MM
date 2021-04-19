import pandas as pd
import json
import re
import os
import copy
from shutil import copyfile

from clustEHR_MM.module_edit_functions import get_edit_states, transition_multiplier,rename_states
from clustEHR_MM.full_dataset_out import demographics, get_age_df, get_binary_df, ajacency
import clustEHR_MM.synthea_functions as sf

def write_out(disease):
    dis_dict = disease_dict[disease]['states']
    states_list = ['Initial','prevelence']
    top_states = {k:v for k,v in dis_dict.items() if k in states_list}
    bottom_states = {k:v for k,v in dis_dict.items() if k not in states_list}
    disease_path = 'andre_test/modules/module_bases/' + disease
    other_dict = disease_dict[disease].copy()
    del other_dict['states']
    if os.path.isdir(disease_path) == False:
        os.mkdir(disease_path)
    with open(disease_path + '/' + disease + '_top.json','w') as out_top:
        json.dump(top_states,out_top)
    with open(disease_path + '/' + disease + '_bottom.json','w') as out_bottom:
        json.dump(bottom_states,out_bottom)
    with open(disease_path + '/' + disease + '_framework.json','w') as out_fw:
        json.dump(other_dict,out_fw)

def write_conditional(disease):
    disease_cond = {
        'breast_cancer':'breast_cancer_condition',
        'colorectal_cancer':'colorectal_cancer',
        'copd':'copd_variant',
        'dementia':'Type of Alzheimer\'s',
        'dermatitis':'dermatitis',
        'fibromyalgia':'fibromyalgia',
        'gallstones':'gallstones',
        'gout':'gout',
        'lung_cancer':'Lung Cancer',
        'lupus':'lupus',
        'rheumatoid_arthritis':'rheumatoid_arthritis',
        'sore_throat':'Sore Throat Condition'
    }

    if_dict = {
        "condition_type": "Attribute",
        "attribute": disease_cond[disease],
        "operator": 'is not nil',
    }

    return if_dict

def write_top_dict(dis_top_dict,disease,mult):

    end_transition = 'Initial_new'

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

    if disease_top['Initial_new']['type'] == 'Initial':
        disease_top['Initial_new']['type'] = 'Simple'

    if old_top['Initial_old']['type'] == 'Initial':
        old_top['Initial_old']['type'] = 'Simple'


    new_top.update(disease_top)
    new_top.update(old_top)
    return new_top

def write_new_folder(disease_a,disease_b,out_folder,mult,test = False):

    with open('andre_test/modules/module_bases/' + disease_b + '/' + disease_b + '_top.json') as ft:
        top_dict = json.load(ft)

    with open('andre_test/modules/module_bases/' + disease_b + '/' + disease_b + '_bottom.json') as fb:
        bottom_dict = json.load(fb)

    with open('andre_test/modules/module_bases/' + disease_b + '/' + disease_b + '_framework.json') as fw:
        fw_dict = json.load(fw)

    new_disease = copy.deepcopy(fw_dict)
    if test:
        new_top = write_test_dict(top_dict, disease_a, mult)
    else:
        new_top = write_top_dict(top_dict,disease_a,mult)
    new_disease['states'] = {**new_top,**bottom_dict}


    with open(out_folder + '/' + disease_b + '.json',"w") as out:
        json.dump(new_disease,out)

def one_group(group_df,out_file,module_out,population):
    if isinstance(group_df,str):
        if '.csv' in group_df:
            group_df = pd.read_csv(group_df)

    if os.path.isdir(out_file) == False:
        os.mkdir(out_file)
    if os.path.isdir(module_out) == False:
        os.mkdir(out_file + '/' + module_out)
    for i in group_df.iterrows():
        write_new_folder(
            disease_a = i[1]['disease_a'],
            disease_b = i[1]['disease_b'],
            out_folder = out_file + '/' + module_out,
            mult = i[1]['rates'])

    copy_modules = [i for i in os.listdir('andre_test/modules/modules') if i not in os.listdir(out_file + '/' + module_out)]
    for i in copy_modules:
        copyfile('andre_test/modules/modules/' + i, out_file + '/' + module_out+ '/' + i)
    sf.run_synthea(module_file = out_file + '/' +module_out, pop = population,file_out = out_file,seed = 4)


def create_synthetic_data(group_df,out_file,module_out,population,age_df,bin_df,adjacency,cond_dict):

    one_group(group_df, out_file, module_out, population)
    os.mkdir(out_file +'/results')
    pats = pd.read_csv(out_file + '/csv/patients.csv')
    obs = pd.read_csv(out_file + '/csv/observations.csv')
    conds = pd.read_csv(out_file + '/csv/conditions.csv')
    demog_df = demographics(pats,obs)
    if age_df:
        age = get_age_df(pats,conds,cond_dict)
        age = pd.merge(demog_df,age,how = 'inner',on = 'PATIENT')
        age.to_csv(out_file +'/results/patient_disease_age.csv',index=False)
    if bin_df:
        df_bin = get_binary_df(conds,cond_dict)
        df_bin = pd.merge(demog_df,df_bin,how = 'inner',on = 'PATIENT')
        df_bin.to_csv(out_file + '/results/patient_disease_binary.csv',index=False)
    if adjacency:
        adj = ajacency(get_binary_df(conds, cond_dict))
        adj.to_csv(out_file +'/results/adjacency_matrix.csv')


if __name__ == '__main__':

    if os.path.exists('andre_test/modules/module_bases') == False:
        diseases = os.listdir('andre_test/modules/modules')
        diseases = [re.sub('\.json', '', i) for i in diseases if '.json' in i]

        disease_dict = {}
        for i in diseases:
            file = 'andre_test/modules/modules/' + i + '.json'
            with open(file, encoding='iso-8859-1') as fb:
                disease_dict[i] = json.load(fb)

        states = {i: list(disease_dict[i]['states'].keys()) for i in diseases}
        os.mkdir('andre_test/modules/module_bases')
        [write_out(i) for i in diseases]

    test_list = ['test_1','test_2','test_3']

    with open('data/processed/disease_conditions.json') as gf:
        cond_dict = json.load(gf)

    for i in test_list:
        input_string = 'andre_test/input/' + i + '.csv'
        out_file = 'andre_test/output/' + i
        if os.path.exists(out_file) == False:
            os.mkdir(out_file)
        create_synthetic_data(
            input_string,
            out_file = out_file,
            module_out = 'modules',
            population = 100000,
            age_df = False,
            bin_df = True,
            adjacency = False,
            cond_dict = cond_dict
        )
