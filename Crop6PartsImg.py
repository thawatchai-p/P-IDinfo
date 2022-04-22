import importlib.util
import sys

# For illustrative purposes.
name = 'PIL'

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
    !pip3 install Pillow
    
import gc
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pathlib import Path
from PIL import Image
import regex as re
from tqdm import tqdm

def get_file_list(dir_name):
    
    ''' For the given path, get the List of all files in the directory tree '''
    
    # create a list of file and sub directories 
    # names in the given directory 
    list_of_file = os.listdir(dir_name)
    all_files = []
    
    # Iterate over all the entries
    for entry in list_of_file:
        # Create full path
        full_path = os.path.join(dir_name, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(full_path):
            all_files = all_files + get_file_list(full_path)
        else:
            all_files.append(full_path)
                
    return all_files

def crop6parts_image(name: Path):
    
    ''' Crop the image of P&ID into 6 parts for better model training '''
    
    # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
    os.chdir(name)
    
    print('Cropping text have been proceeding.')
    
    raster_path = ".\\PNG"
    list_raster_files = get_file_list(raster_path)
    
    for idx in tqdm(range(len(list_raster_files))):
        
        file_raster_location = list_raster_files[idx]
        
        listname = re.split(r'\\|\.', file_raster_location)
        filename = listname[-2]
        filename = re.sub('"','',filename)
        filename = re.sub('/','_',filename)
        save_cropped_folder = '.\\Crop6PartsImg'
        trim_char = ['','PNG',filename,'png']
        
        if not os.path.exists(save_cropped_folder):
            os.makedirs(save_cropped_folder)
        
        if bool(len(list_raster_files) != 0):
            prior_folder = [folder for folder in listname if folder not in trim_char]
            prior_folder = "".join(prior_folder)
            saveinfo_path = save_cropped_folder+'\\'+"".join(prior_folder)+'\\'+filename+'\\'
            if not os.path.exists(saveinfo_path): # Check the whether if existing folder is created
                os.makedirs(saveinfo_path)           

        else:
            saveinfo_path = save_cropped_folder+'\\'+filename+'\\'
            if not os.path.exists(saveinfo_path): # Check the whether if existing folder is created
                os.makedirs(saveinfo_path)

        print('Saving cropped images file at:', saveinfo_path)
        
        save_prefix = saveinfo_path+filename
        
        with Image.open(file_raster_location) as img:
            height = img.height
            width = img.width
            
            one_third_height = (1/3)*height
            two_third_height = (2/3)*height
            one_third_width = (1/3)*width
            two_third_width = (2/3)*width
            
            img_crop_q1 = img.crop((width/2, 0, width, height/2))
            img_crop_q2 = img.crop((0, 0, width/2, height/2))
            img_crop_q3 = img.crop((0, height/2, width/2, height))
            img_crop_q4 = img.crop((width/2, height/2, width, height))
            img_crop_ov = img.crop((one_third_width, 0, two_third_width, height))
            img_crop_oh = img.crop((0, one_third_height, width, two_third_height))
            
            img_crop_q1.save(save_prefix+'_q1.png')
            img_crop_q2.save(save_prefix+'_q2.png')
            img_crop_q3.save(save_prefix+'_q3.png')
            img_crop_q4.save(save_prefix+'_q4.png')
            img_crop_ov.save(save_prefix+'_ov.png')
            img_crop_oh.save(save_prefix+'_oh.png')
            
    print('Image cropping is now finished!!!')
    gc.collect()
    
# set your working directory:
DIR = Path("D:\\ENQA\\Training\\VISTEC\\[2021] Data Science Lv2\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!

crop6parts_image(DIR)
