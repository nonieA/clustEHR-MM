import json
import re
import os
import pandas as pd

disease_a = 'Acute gastroenteritis (disorder)'
disease_b = 'Stomatitis'

conditions = pd.read_csv('fake_out/csv/conditions.csv')
conditions2 = conditions[['PATIENT','DESCRIPTION']]
conditions2['value'] = 1
cond3 = conditions2.groupby(['PATIENT', 'DESCRIPTION'])['value'].count().reset_index()
cond4 = cond3.pivot_table(index='PATIENT', columns='DESCRIPTION', values='value', fill_value=0)


no_disease_a = len(cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 0)])
with_disease_a = len(cond4[(cond4[disease_b] == 1) & (cond4[disease_a] == 1)])
just_disease_a = len(cond4[cond4[disease_a] == 1])
