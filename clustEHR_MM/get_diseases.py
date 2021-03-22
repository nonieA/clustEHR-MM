import pandas as pd
import subprocess
import os
import copy
import json

def run_basic_module(module,p = 100,out_file = 'test_data'):
    print(module)
    file_out = out_file + module

    module_list = ['anemia',
                   'asthma',
                   'breast_cancer',
                   'bronchitis',
                   'colorectal_cancer',
                   'dermatitis',
                   'fibromyalgia',
                   'hypothyroidism']

    if module in module_list:
        module = module + '*'


    synth_cmd = ("java -jar clustEHR_MM/synthea-with-dependencies.jar -a 18-100 -m " +
                 module +
                 " -p " +
                 str(p) +
                 " -s 4 -c clustEHR_MM/synthea_config.txt --exporter.baseDirectory " + file_out)


    run_thing = subprocess.run(synth_cmd, stdout=subprocess.PIPE)
    if run_thing.stdout.decode('utf-8').find('[0 loaded]') > -1:
        raise ValueError('so the disease input doesnt link to a module')

    conditions = pd.read_csv(file_out + '/csv/conditions.csv')

    return list(conditions['DESCRIPTION'].unique())

def get_uniques(disease,og_dict):
    copy_dict = copy.deepcopy(og_dict)
    copy_dict.pop(disease)
    disease_list = set([j for i in copy_dict.values() for j in i])
    return_list = [i for i in og_dict[disease] if i not in disease_list]
    return return_list

if __name__ == '__main__':

    module_list = os.listdir('modules/module_bases')
    cond_dict = {i:run_basic_module(i) for i in module_list}
    unique_conds = {k:get_uniques(k,cond_dict) for k in cond_dict.keys()}
    redo_list = [k for k,v in unique_conds.items() if len(v) == 0]
    cond_dict2 = {i: run_basic_module(i,p = 10000,out_file = 'test_data2') for i in redo_list}
    new_cond_dict = {k: cond_dict2[k] if k in cond_dict2.keys() else cond_dict[k] for k in cond_dict.keys()}
    unique_conds2 ={k:get_uniques(k,new_cond_dict) for k in new_cond_dict.keys()}
    new_no = [k for k,v in unique_conds2.items() if len(v) == 0]
    print(new_no)
    final_conds = {k:v for k,v in unique_conds2.items() if k not in new_no}

    with open('data/processed/disease_conditions.json','w') as gf:
        json.dump(final_conds,gf)

