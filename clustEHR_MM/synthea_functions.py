import json
import os
import clustEHR_MM.module_edit_functions as mef
import subprocess
import pandas as pd

def run_synthea(disease,module_file, pop,file_out,seed,addition):

        module_str = 'clustEHR_MM/'+module_file + '/' + disease + '_' + addition

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

def run_function(disease_a,disease_b,module_out,csv_out,addition,pop,seed,mult):
        mef.write_new_folder(disease_a,disease_b,module_out,mult,addition)
        run_synthea(disease_b,module_out,pop,csv_out,seed,addition)

def get_counts(disease_a,disease_b,csv_file):
        conditions = pd.read_csv(csv_file + '/csv/conditions.csv')
        conditions2 = conditions[['PATIENT','DESCRIPTION']]
        conditions2['value'] = 1
        cond3 = conditions2.groupby(['PATIENT','DESCRIPTION'])['value'].count().reset_index()
        cond4 = cond3.pivot_table(index='PATIENT',columns='DESCRIPTION',values='value',fill_value=0)
        no_disease_a = cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 0)]
        with_disease_a = cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 1)]
        out_dict = {disease_b + '_no_' + disease_a: len(no_disease_a),
                    disease_b + '_and_' + disease_a: len(with_disease_a)}
        return out_dict

if __name__ == '__main__':
        mef.write_new_folder('Diabetes','gout','test',2,'test')
        run_synthea('gout','test',10000,'test_out',4,'test')
        conditions = pd.read_csv('test_out/csv/conditions.csv')
        conditions2 = conditions[['PATIENT','DESCRIPTION']]
        conditions2['value'] = 1
        cond3 = conditions2.groupby(['PATIENT','DESCRIPTION'])['value'].count().reset_index()
        cond4 = cond3.pivot_table(index='PATIENT',columns='DESCRIPTION',values='value',fill_value=0)
        gout = cond4[(cond4['Gout'] == 1) & (cond4['Diabetes'] == 0)]
        gout_diabetes = cond4[(cond4['Gout'] == 1) & (cond4['Diabetes'] == 1)]

        base_line = get_counts('Diabetes','Gout','base_line')

        run_function('Diabetes','gout','test3','test_out3','test',10000,4,2)
        test = get_counts('Diabetes','Gout','test_out3')
        test_out = pd.read_csv('test_out3/csv/conditions.csv')