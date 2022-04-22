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

def resized_drawing(name: Path, dpi=216):
    
    ''' Resize the drawing of specific folders into required size by using pillow library'''
    
    # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
    os.chdir(name)
    
    print('Drawing resize have been proceeding.')
    
    raster_folder = ".\\PNG"
    list_raster_files = get_file_list(raster_folder)
         
    for idx in tqdm(range(len(list_raster_files))):
        
        file_location = list_raster_files[idx]
        
        with Image.open(file_location) as img:
            
            # Provide the target width and height of the image
            # l: 4077 x 2880 --- M: 2437 x 1721
            (width, height) = (2437, 1721)
            
            img_resized = img.resize((width, height), resample=Image.Resampling(1))
            
            listname = re.split(r'\\|\.', file_location)
            filename = listname[-2]
            save_resized_folder = '.\\Resized'
            trim_char = ['','PNG',filename,'png']

            if not os.path.exists(save_resized_folder):
                os.makedirs(save_resized_folder)

            # Save file
            if bool(len(list_raster_files) != 0):

                prior_folder = [folder for folder in listname if folder not in trim_char]
                prior_folder = "".join(prior_folder)
                if not os.path.exists(save_resized_folder+'\\'+prior_folder): # Check the whether if existing folder is created
                    os.makedirs(save_resized_folder+'\\'+prior_folder)
                saveinfo_path = save_resized_folder+'\\'+prior_folder+'\\'+filename+'.png'
                print('Saving resized image file at:', saveinfo_path)
            else:
                saveinfo_path = save_resized_folder+'\\'+filename+'.png'
                
        # Save the resized image and reduce dpi from 300 to 216
        img_resized.save(saveinfo_path, dpi=(dpi, dpi))
    
# set your working directory:
DIR = Path("D:\\ENQA\\Training\\VISTEC\\[2021] Data Science Lv2\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!

resized_drawing(DIR, dpi=96)
