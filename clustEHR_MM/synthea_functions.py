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

        mef.write_new_folder('Diabetes','gout','test2',4,'test2')
        run_synthea('gout','test2',10000,'test_out2',4,'test2')
        bconditions = pd.read_csv('test_out2/csv/conditions.csv')
        bconditions2 = bconditions[['PATIENT','DESCRIPTION']]
        bconditions2['value'] = 1
        bcond3 = bconditions2.groupby(['PATIENT','DESCRIPTION'])['value'].count().reset_index()
        bcond4 = bcond3.pivot_table(index='PATIENT',columns='DESCRIPTION',values='value',fill_value=0)
        bgout = bcond4[(bcond4['Gout'] == 1) & (cond4['Diabetes'] == 0)]
        bgout_diabetes = bcond4[(bcond4['Gout'] == 1) & (bcond4['Diabetes'] == 1)]
