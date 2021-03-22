import clustEHR_MM.module_edit_functions as mef
import subprocess
import pandas as pd
import json

def run_synthea(disease,module_file, pop,file_out,seed,addition):

        module_str = module_file + '/' + disease + '_' + addition

        synth_cmd = ("java -jar clustEHR_MM/synthea-with-dependencies.jar -a 18-100 -d " +
                 module_str +
                 " -p " +
                 str(pop) +
                 " -s " +
                 str(seed) +
                 " -c clustEHR_MM/synthea_config.txt --exporter.baseDirectory " +
                 file_out)

        run_thing = subprocess.run(synth_cmd, stdout=subprocess.PIPE)
        if run_thing.stdout.decode('utf-8').find('[0 loaded]') > -1:
                raise ValueError('so the disease input doesnt link to a module')

def run_function(disease_a,disease_b,module_out,csv_out,addition,pop,seed,mult,test):
        mef.write_new_folder(disease_a,disease_b,module_out,mult,addition,test)
        run_synthea(disease_b,module_out,pop,csv_out,seed,addition)

def get_counts(disease_a,disease_b,csv_file,cond_dict):
        conditions = pd.read_csv(csv_file + '/csv/conditions.csv')
        conditions2 = conditions[['PATIENT','DESCRIPTION']]

        if disease_b != 'Stomatitis':
                conditions2['DESCRIPTION'] = conditions2['DESCRIPTION'].apply(
                        lambda x: disease_b if x in cond_dict[disease_b] else x)

                conditions2['DESCRIPTION'] = conditions2['DESCRIPTION'].apply(
                        lambda x: disease_a if x in cond_dict[disease_a] else x)

        conditions2['value'] = 1
        cond3 = conditions2.groupby(['PATIENT','DESCRIPTION'])['value'].count().reset_index()
        cond4 = cond3.pivot_table(index='PATIENT',columns='DESCRIPTION',values='value',fill_value=0)
        no_disease_a = cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 0)]
        with_disease_a = cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 1)]
        just_disease_a = cond4[cond4[disease_a] == 1]
        out_dict = {disease_b + '_no_' + disease_a: len(no_disease_a),
                    disease_b + '_and_' + disease_a: len(with_disease_a),
                    'just_' + disease_a: len(just_disease_a)}
        return out_dict

if __name__ == '__main__':

        base_line = get_counts('Diabetes','Gout','base_line')

        run_function('diabetes','gout','test3','test_out3','test',10000,4,2)
        test = get_counts('Diabetes','Gout','test_out3')

        test_out = pd.read_csv('test_out4/csv/conditions.csv')
        test_out_counts = get_counts('Diabetes','Stomatitis','test_out3')

        run_function('Diabetes', 'gout', 'test4', 'test_out4', 'test', 10000, 4, 2)
        test_out_counts = get_counts('Diabetes', 'Stomatitis', 'test_out4')

        run_function('Diabetes', 'gout', 'test5', 'test_out5', 'test', 10000, 4, 2)
        test_out_counts = get_counts('Diabetes', 'Stomatitis', 'test_out4')
        run_synthea('gout', 'test4', 10000, 'test_out8', 4, 'test')
        test_out_counts = get_counts('Diabetes', 'Stomatitis', 'test_out8')

        run_function('diabetes', 'gout', 'test8', 'test_out8', 'test', 10000, 4, 2)
        test_out_counts = get_counts('Diabetes', 'Stomatitis', 'test_out8')

        run_synthea('gout', 'test9', 10000, 'test_out9', 4, 'test')
        test_out_counts3 = get_counts('Diabetes', 'Stomatitis', 'test_out9')

        run_function('diabetes', 'gout', 'test10', 'test_out10', 'test', 10000, 4, 2)
        test_out_counts = get_counts('Diabetes', 'Stomatitis', 'test_out10')

        with open('data/processed/disease_conditions.json') as gf:
                test_dict = json.load(gf)

        base_line = pd.read_csv('base_line/csv/conditions.csv')
        disease_a = 'copd'
        disease_b = 'gout'

        conditions2 = base_line[['PATIENT', 'DESCRIPTION']]

        conditions2['value'] = 1
        cond3 = conditions2.groupby(['PATIENT', 'DESCRIPTION'])['value'].count().reset_index()
        cond4 = cond3.pivot_table(index='PATIENT', columns='DESCRIPTION', values='value', fill_value=0)
        no_disease_a = cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 0)]
        with_disease_a = cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 1)]
        out_dict = {disease_b + '_no_' + disease_a: len(no_disease_a),
                    disease_b + '_and_' + disease_a: len(with_disease_a)}
