import json
import re
import os
import pandas as pd

disease_a = 'breast_cancer'
disease_b = 'gout'
pop = 10000
with open('data/processed/disease_conditions.json') as gf:
    cond_dict = json.load(gf)

conditions = pd.read_csv('output/csv/conditions.csv')
conditions2 = conditions[['PATIENT','DESCRIPTION']]

conditions2['DESCRIPTION'] = conditions2['DESCRIPTION'].apply(
    lambda x: disease_a if x in cond_dict[disease_a] else x)


conditions2['DESCRIPTION'] = conditions2['DESCRIPTION'].apply(
    lambda x: disease_b if x in cond_dict[disease_b] else x)

conditions2['value'] = 1
cond3 = conditions2.groupby(['PATIENT', 'DESCRIPTION'])['value'].count().reset_index()
cond4 = cond3.pivot_table(index='PATIENT', columns='DESCRIPTION', values='value', fill_value=0)


no_disease_a = len(cond4[(cond4[disease_b] > 0) & (cond4[disease_a] == 0)])
with_disease_a = len(cond4[(cond4[disease_b] > 0) & (cond4[disease_a] > 0)])
just_disease_a = len(cond4[cond4[disease_a] > 0])
with_disease_a_prev = with_disease_a/just_disease_a
no_d_a_prev = no_disease_a/(pop-just_disease_a)
print(with_disease_a_prev)
print(no_d_a_prev)
print(with_disease_a_prev/no_d_a_prev)


asthma_conds = pd.read_csv('test/csv_name_test/asthma_careplan_not_nil/csv/conditions.csv')
asthma_conds = asthma_conds[['PATIENT','DESCRIPTION']]
asthma_conds['DESCRIPTION_2'] = asthma_conds['DESCRIPTION'].apply(lambda x: 'asthma' if x in cond_dict['asthma'] else x)

stom_pats = asthma_conds['PATIENT'][asthma_conds['DESCRIPTION'] == 'Stomatitis'].tolist()
asthma_pats = asthma_conds['PATIENT'][asthma_conds['DESCRIPTION_2'] == 'asthma'].tolist()
stom_no_asthma = [i for i in stom_pats if i not in asthma_pats]

sna_conds = asthma_conds['DESCRIPTION'][asthma_conds['PATIENT'].isin(stom_no_asthma)].unique()

def get_all_conds(outfile,disease_a,cond_dict):
    conditions = pd.read_csv(outfile + '/csv/conditions.csv',usecols=['PATIENT','DESCRIPTION'])
    encounters = pd.read_csv(outfile + '/csv/encounters.csv',usecols=['PATIENT','REASONDESCRIPTION']).rename(columns={'REASONDESCRIPTION':'DESCRIPTION'})
    careplans = pd.read_csv(outfile + '/csv/careplans.csv',usecols=['PATIENT','REASONDESCRIPTION']).rename(columns={'REASONDESCRIPTION':'DESCRIPTION'})
    medications = pd.read_csv(outfile + '/csv/medications.csv')
    meds = medications[['PATIENT', 'CODE']]
    meds = meds[meds['CODE'].isin([311989,1094107])]
    meds['DESCRIPTION'] = disease_a
    meds = meds.drop('CODE', axis=1)

    conditions2 = pd.concat([conditions,meds])
    conditions2 = conditions2.dropna(subset = ['DESCRIPTION'])
    if disease_a in cond_dict.keys():
        conditions2['DESCRIPTION'] = conditions2['DESCRIPTION'].apply(
            lambda x: disease_a if x in cond_dict[disease_a] else x)

    conditions2['value'] = 1
    cond3 = conditions2.groupby(['PATIENT', 'DESCRIPTION'])['value'].count().reset_index()
    cond4 = cond3.pivot_table(index='PATIENT', columns='DESCRIPTION', values='value', fill_value=0)

    no_disease_a = len(cond4[(cond4[disease_b] > 0) & (cond4[disease_a] == 0)])
    with_disease_a = len(cond4[(cond4[disease_b] > 0) & (cond4[disease_a] > 0)])
    just_disease_a = len(cond4[cond4[disease_a] > 0])
    print(no_disease_a)
    print(with_disease_a)
    print(just_disease_a)

conds = pd.read_csv('output/csv/conditions.csv')

conds = conds[['PATIENT','DESCRIPTION']]

def replace_disease(var):
    cond_list = [j for i in cond_dict.values() for j in i ]
    if var in cond_list:
        for k,v in cond_dict.items():
            if var in v:
                return k
    else:
        return var


conds['DESCRIPTION2'] = conds['DESCRIPTION'].apply(replace_disease)

conds2 = conds[conds['DESCRIPTION2'].isin(list(cond_dict.keys()))]

conds2 = conds2.drop(columns='DESCRIPTION')
conds2['value'] = 1
cond3 = conds2.groupby(['PATIENT', 'DESCRIPTION2'])['value'].count().reset_index()

conds_count = cond3.groupby('DESCRIPTION2').count()