import importlib.util
import sys

# For illustrative purposes.
name = 'rstr'

if name in sys.modules:
    print(f"{name!r} already in sys.modules")
elif (spec := importlib.util.find_spec(name)) is not None:
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    print(f"{name!r} has been imported")
else:
    print(f"can't find the {name!r} module")
    print(f"installation {name!r} is proceeding...")
    ! pip install name
    
import numpy as np
import pandas as pd
import matplotlib
import rstr
import os

def pipe_size():
    pipe_size = np.array(['1/4','1/2','3/4','1','1 1/4','1 1/2','2 1/2','3','3 1/2'])
    pipe_size_seq = np.array([size.astype(str) for size in np.arange(2,50,2)]).reshape(-1)
    pipe_size = np.concatenate((pipe_size, pipe_size_seq))
    return pipe_size

def piping_gen_adu1(num=10):
    pipesize = pipe_size()
    process = ['AD','AF','AII','AIP','AIW','AM','AML','AMR','ATB','CD','CG','CL','CO2','CPL','CPM','CPH','CR','FA','FG','FO','GV','GW',
                'H','HGO','HN','IL','KERO','LGO','LN','LPG','MX','NH','NL','P','PPAL','PPAV','SAL','SAN','SHC','SH','SHO','SL','SM','TU',
                'WB','WBW','WCI','WCS','WDS','WF','WFW','WGR','WH','WO','WP','WR','WS','WSS','WSW','WW','WWT','WWO']
    pip_class = ['A11','A11A','A12','A13','A14','A15','A16','A17','A22','A23','A24','A25','A27','A42','A44','A45',
                  'D11','D19','D41','D49','C14','C24','C42','G11A','G11B','H49','H59','J49','J59','L42']
    insulation = ['','-30W','-50W','-100W','-150W','-30D','-25S']
    line_list = []
    for i in range(0,num):
        size_rand = ''.join(np.random.choice(pipesize, 1))
        process_rand = ''.join(np.random.choice(process, 1))
        pclass_rand = ''.join(np.random.choice(pip_class, 1))
        insu_rand = ''.join(np.random.choice(insulation, 1))
        s = size_rand + '"-' + rstr.xeger(r'[0-9]{8}') + '-' + pclass_rand + insu_rand
        line_list.append(s)
    
    return line_list 

def piping_gen_btx(num=10):
    pipesize = pipe_size()
    process = ['AF','AII','AIP','CL','CG','CPL','CPH','FA','FG','FO','LD','HD','NL','SFLD','SFLL','SFLR','SH','SL','SM',
               'WDS','WF','WP','WPR','WR','WS','WWO']
    pip_class = ['A11','A13','A14','A17','A22','A25','D11','G11','G12']
    insulation = ['','-30W','-50W','-100W','-150W','-30D','-25S']
    line_list = []
    for i in range(0,num):
        size_rand = ''.join(np.random.choice(pipesize, 1))
        process_rand = ''.join(np.random.choice(process, 1))
        pclass_rand = ''.join(np.random.choice(pip_class, 1))
        insu_rand = ''.join(np.random.choice(insulation, 1))
        s = size_rand + '"-' + rstr.xeger(r'[0-9]{8}') + '-' + pclass_rand + insu_rand
        line_list.append(s)
    
    return line_list 

def main(num):
    num_plant = int(num / 2) # 2 is numbers of plant (adu1, btx)
    adu1 = piping_gen_adu1(num_plant)
    btx = piping_gen_btx(num_plant)
    total = adu1 + btx
    return total

if __name__ == '__main__':
    main()
