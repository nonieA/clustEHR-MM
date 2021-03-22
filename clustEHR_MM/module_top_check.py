import json
import os

def module_tops(disease):
    with open('modules/module_bases/'+disease + '/' + disease + '_top.json') as t:
        disease_top = json.load(t)

    with open('modules/module_bases/' +disease + '/'+ disease + '_framework.json') as fw:
        disease_fw = json.load(fw)

    disease_fw['states'] = disease_top

    with open('modules/top_check/' + disease +'_check.json','w') as out:
        json.dump(disease_fw,out)

if __name__ == '__main__':

    diseases = os.listdir('modules/module_bases')
    [module_tops(i) for i in diseases]