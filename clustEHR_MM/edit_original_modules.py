import json
import os
import re


def write_out(disease):
    dis_dict = disease_dict[disease]['states']
    top_states = {k:v for k,v in dis_dict.items() if k in state_dict[disease]}
    bottom_states = {k:v for k,v in dis_dict.items() if k not in state_dict[disease]}
    disease_path = 'modules/module_bases/' + disease
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

if __name__ == '__main__':

    diseases = os.listdir('modules/modules')
    diseases = [re.sub('\.json','',i) for i in diseases if '.json' in i]

    disease_dict = {}
    for i in diseases:
        file = 'modules/modules/' + i + '.json'
        with open(file,encoding='iso-8859-1') as fb:
            disease_dict[i] = json.load(fb)

    states = {i:list(disease_dict[i]['states'].keys()) for i in diseases}

    state_dict = {'allergic_rhinitis':states['allergic_rhinitis'][0:3],
                'anemia___unknown_etiology':states['anemia___unknown_etiology'][0:6],
                'appendicitis':states['appendicitis'][0:2],
                'asthma':states['asthma'][0:2],
                'atopy':states['atopy'][0],
                'attention_deficit_disorder':states['attention_deficit_disorder'][0],
                'breast_cancer':['Initial','Male','Female'],
                'bronchitis':states['bronchitis'][0],
                'cerebral_palsy':['Initial','Male','Female','Age_and_Applicable_Time_Guard'],
                'colorectal_cancer':states['colorectal_cancer'][0:1],
                'congestive_heart_failure':['Initial','Age Guard','Determine CHF'],
                'copd':states['copd'][0:3],
                'cystic_fibrosis':['Initial','Potential_Onset'],
                'dementia':states['dementia'][0],
                'dermatitis':states['dermatitis'][0:3],
                'ear_infections':states['ear_infections'][0:2],
                'epilepsy':states['epilepsy'][0],
                'fibromyalgia':states['fibromyalgia'][0],
                'gallstones':['Initial','Female','Male'],
                'gout':states['gout'][0],
                'hypertension':['Initial','Wellness_Encounter','Included','Excluded','Wait Until Next Checkup',],
                'hypothyroidism':['Initial','Age delay'],
                'lung_cancer':states['lung_cancer'][0:2],
                'lupus':states['lupus'][0],
                'metabolic_syndrome_disease':['Initial', 'Initial_Kidney_Health', 'Initial_Eye_Health',
                                              'Initial_Nerve_Health', 'Age_Guard', 'Chance_to_Onset_Hypertension',
                                              'Veteran', 'Non_Veteran','Onset_Hypertension','No_Hypertension'],
                'mTBI':['Initial', 'veteran delay'],
                'opioid_addiction':['Initial', 'Guard', 'General_Population'],
                'osteoarthritis':['Initial', 'Veteran', 'Non_Veteran', 'Delay_Pre_Arthritis'],
                'osteoporosis':['Initial', 'Female', 'Male'],
                'rheumatoid_arthritis':states['rheumatoid_arthritis'][0],
                'sepsis':['Initial','Age_guard'],
                'sinusitis':states['sinusitis'][0:1],
                'sore_throat':states['sore_throat'][0:1],
                'spina_bifida':['Initial','Enter_Spina_Bifida'],
                'urinary_tract_infections':states['urinary_tract_infections'][0]
                              }

    [write_out(i) for i in state_dict.keys()]