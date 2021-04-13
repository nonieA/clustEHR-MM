import pandas as pd
import clustEHR_MM.synthea_functions as sf
from clustEHR_MM.module_edit_functions import write_new_folder

import os
import datetime as dt
from argparse import ArgumentParser

def one_group(group_df,out_file,module_out,population):
    if isinstance(group_df,str):
        if '.csv' in group_df:
            group_df = pd.read_csv(group_df)

    if os.path.isdir(out_file) == False:
        os.mkdir(out_file)

    sf.create_folders(module_out)
    for i in group_df.iterrows():
        write_new_folder(
            disease_a = i[1]['disease_a'],
            disease_b = i[1]['disease_b'],
            out_folder = module_out,
            mult = i[1]['rates'])


    sf.copy_folders(module_out)

    sf.run_synthea(module_file = module_out, pop = population,file_out = out_file,seed = 4)

def replace_disease(var,cond_dict):
    cond_list = [j for i in cond_dict.values() for j in i]
    if var in cond_list:
        for k, v in cond_dict.items():
            if var in v:
                return k
    else:
        return var


def get_binary_df(conds,cond_dict):
    conds = conds[['PATIENT','DESCRIPTION']]
    conds['DESCRIPTION'] = conds['DESCRIPTION'].apply(lambda x: replace_disease(x,cond_dict))
    conds = conds[conds['DESCRIPTION'].isin(list(cond_dict.keys()))]
    conds['value'] = 1
    conds = conds.groupby(['PATIENT', 'DESCRIPTION'])['value'].sum().reset_index()
    conds['value'] = 1
    conds = conds.pivot_table(index='PATIENT', columns='DESCRIPTION', values='value', fill_value=0)

    return conds

def demographics(pats,obs):
    pats_short = pats[['Id','BIRTHDATE','DEATHDATE','RACE','GENDER']].rename(columns = {'Id':'PATIENT'})
    tobacco = obs[obs['DESCRIPTION'] == 'Tobacco smoking status NHIS'][['DATE','PATIENT','VALUE']]
    tobacco = tobacco.sort_values(
        'DATE',
        axis = 0,
        ascending= False).drop_duplicates('PATIENT').drop(columns='DATE').rename(columns = {'VALUE':'Smoking status'})

    bmi = obs[obs['DESCRIPTION'] == 'Body Mass Index'][['DATE','PATIENT','VALUE']]
    bmi = bmi.sort_values(
        'DATE',
        axis = 0,
        ascending= False).drop_duplicates('PATIENT').drop(columns='DATE').rename(columns = {'VALUE':'BMI'})

    pats_new = pd.merge(left= pats_short, right=tobacco,how='left',on = 'PATIENT')
    pats_new = pd.merge(left=pats_new, right=bmi, how='left', on='PATIENT')
    return pats_new

def get_age(date1,date2):
    days = dt.datetime.strptime(date1, '%Y-%m-%d') - dt.datetime.strptime(date2, '%Y-%m-%d')
    return round(days.days/365.25)

def get_age_df(pats,conds,cond_dict):
    conds = conds[['START','PATIENT','DESCRIPTION']]
    conds['DESCRIPTION'] = conds['DESCRIPTION'].apply(lambda x: replace_disease(x,cond_dict))
    conds = conds[conds['DESCRIPTION'].isin(cond_dict.keys())]
    conds = conds.sort_values(
        'START',
        axis = 0,
        ascending= False).drop_duplicates(['PATIENT','DESCRIPTION'])
    pats_small = pats[['Id','BIRTHDATE']].rename(columns = {'Id':'PATIENT'})
    conds = pd.merge(left = pats_small,right = conds,how = 'left',on = 'PATIENT').dropna()
    conds['ONSET_AGE'] = conds[['START','BIRTHDATE']].apply(lambda x: get_age(x[0],x[1]), axis =1)
    conds = conds.drop(columns= ['START','BIRTHDATE'])
    conds = conds.pivot(index='PATIENT',columns = 'DESCRIPTION',values='ONSET_AGE')
    return conds

def ajacency(df_bin):
    return df_bin.corr(method='pearsonn')

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

def create_argparser():
    parser = ArgumentParser()
    parser.add_argument(
        '--input_file',
        help = 'path to csv with relationships between diseases',
        type = str
    )

    parser.add_argument(
        '--out_file',
        help = 'path where output should be located',
        default='output',
        type = str
    )

    parser.add_argument(
        '--module_out',
        help = 'path to where modules are stored',
        default='output/modules',
        type = str
    )

    parser.add_argument(
        '--population',
        help = 'number of patients to output',
        default=100000,
        type = int
    )

    parser.add_argument(
        '--age_csv',
        help = 'returns csv patients by disease with age of onset of each disease for the patient',
        default= True,
        type=bool
    )

    parser.add_argument(
        '--binary_csv',
        help='returns csv patients by disease with 1 or 0 if disease is present',
        default=True,
        type=bool
    )

    parser.add_argument(
        '--adjacency_csv',
        help='returns adjacency matrix with pearson correlation coefficient between diseases ',
        default=True,
        type=bool
    )

if __name__ == '__main__':

    parser = create_argparser()
    args = parser.parse_args()

    cond_dict = {'allergic_rhinitis': ['Perennial allergic rhinitis with seasonal variation',
                                       'Perennial allergic rhinitis','Seasonal allergic rhinitis'],
                 'appendicitis': ['Appendicitis', 'History of appendectomy','Rupture of appendix'],
                 'asthma': ['Childhood asthma', 'Asthma'],
                 'attention_deficit_disorder': ['Child attention deficit disorder'],
                 'breast_cancer': ['Malignant neoplasm of breast (disorder)'],
                 'bronchitis': ['Acute bronchitis (disorder)'],
                 'cerebral_palsy': ['Cerebral palsy (disorder)', 'Spasticity (finding)', 'Epilepsy (disorder)',
                                    'Intellectual disability (disorder)', 'Gastroesophageal reflux disease (disorder)',
                                    'Poor muscle tone (finding)',  'Excessive salivation (disorder)',
                                    'Unable to swallow saliva (finding)', 'Dribbling from mouth (finding)',
                                    'Constipation (finding)', 'Pneumonia (disorder)', 'Pain (finding)',
                                    'Dislocation of hip joint (disorder)',  'Dystonia (disorder)',
                                    'Retention of urine (disorder)'],
                 'colorectal_cancer': ['Polyp of colon',  'Primary malignant neoplasm of colon',  'Bleeding from anus',
                                       'Protracted diarrhea',  'Secondary malignant neoplasm of colon',
                                       'Recurrent rectal polyp',  'Malignant tumor of colon'],
                 'congestive_heart_failure': ['Chronic congestive heart failure (disorder)'],
                 'copd': ['Pulmonary emphysema (disorder)',  'Chronic obstructive bronchitis (disorder)'],
                 'cystic_fibrosis': ['Female Infertility',  'Cystic Fibrosis',  'Diabetes from Cystic Fibrosis',
                                     'Infection caused by Staphylococcus aureus',
                                     'Sepsis caused by Staphylococcus aureus'],
                 'dementia': ["Alzheimer's disease (disorder)", 'Pneumonia'],
                 'dermatitis': ['Contact dermatitis', 'Atopic dermatitis'],
                 'ear_infections': ['Otitis media'],
                 'epilepsy': ['Seizure disorder',  'History of single seizure (situation)',  'Epilepsy'],
                 'fibromyalgia': ['Primary fibromyalgia syndrome'],
                 'gallstones': ['Acute Cholecystitis', 'Cholelithiasis'],
                 'gout': ['Gout'],
                 'hypothyroidism': ['Idiopathic atrophic hypothyroidism'],
                 'lung_cancer': ['Suspected lung cancer (situation)',  'Non-small cell lung cancer (disorder)',
                                 'Non-small cell carcinoma of lung  TNM stage 1 (disorder)'],
                 'opioid_addiction': ['Chronic pain',  'Impacted molars',  'Chronic intractable migraine without aura',
                                      'Drug overdose'],
                 'osteoarthritis': ['Localized  primary osteoarthritis of the hand',  'Osteoarthritis of hip',
                                    'Osteoarthritis of knee'],
                 'rheumatoid_arthritis': ['Rheumatoid arthritis'],
                 'sinusitis': ['Viral sinusitis (disorder)',  'Chronic sinusitis (disorder)',
                               'Acute bacterial sinusitis (disorder)',  'Sinusitis (disorder)'],
                 'sore_throat': ['Acute viral pharyngitis (disorder)',  'Streptococcal sore throat (disorder)'],
                 'spina_bifida': ['Spina bifida occulta (disorder)',  'Meningomyelocele (disorder)',
                                  'Chiari malformation type II (disorder)',  'Congenital deformity of foot (disorder)'],
                 'urinary_tract_infections': ['Recurrent urinary tract infection',  'Cystitis',
                                              'Escherichia coli urinary tract infection']
                 }

    create_synthetic_data(
        group_df=args.input_file,
        out_file=args.out_file,
        module_out=args.module_out,
        population=args.population,
        age_df=args.age_csv,
        bin_df=args.binary_csv,
        adjacency=args.adjacency_csv,
        cond_dict
    )