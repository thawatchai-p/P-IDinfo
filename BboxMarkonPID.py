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
import os
import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw
import regex as re
import sys
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

def markup_PID(name: Path):
    
    ''' Mark up the bounding box from *.csv file on the rasterized drawing file (*.png or *.jpg) '''
    
    # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
    os.chdir(name)
    
    raster_folder = ".\\PNG"
    csv_folder = ".\\CSV"
    list_raster_files = get_file_list(raster_folder)
    list_csv_files = get_file_list(csv_folder)
    list_data_files = list(zip(list_raster_files,list_csv_files))
    list_data_files = pd.DataFrame(list_data_files, columns=['PNG','CSV'])
    
    for idx in tqdm(list_data_files.index):
        # Get the file location
        raster_filename = list_data_files.loc[idx,'PNG']
        csv_filename = list_data_files.loc[idx,'CSV']
        
        piping_df = pd.read_csv(csv_filename, index_col=0)
        
        # Define related parameters and check the existing save folder
        listname = re.split(r'\\|\.', raster_filename)
        filename = listname[-2]  
        list_folders = os.listdir('.\\PNG')
        save_markup_folder = '.\\MarkUp'
        trim_char = ['','PNG',filename,'png']
    
        if not os.path.exists(save_markup_folder):
            os.makedirs(save_markup_folder)
        
        # Save file location
        if bool(len(list_raster_files) != 0):

            prior_folder = [folder for folder in listname if folder not in trim_char]
            prior_folder = "".join(prior_folder)
            if not os.path.exists(save_markup_folder+'\\'+prior_folder): # Check the whether if existing folder is created
                os.makedirs(save_markup_folder+'\\'+prior_folder)
            saveinfo_path = save_markup_folder+'\\'+prior_folder+'\\'+filename+'.png'
            print('Saving bounding box markup file at:', saveinfo_path)
        else:
            saveinfo_path = save_markup_folder+'\\'+filename+'.png'
        
        with Image.open(raster_filename) as img:
            img = img.convert('RGB')
            draw = ImageDraw.Draw(img)

            for i in piping_df.index:
                lowleft = [float(s) for s in piping_df.loc[i,'LowLeft'].strip()[1:-1].split(", ")]
                upright = [float(s) for s in piping_df.loc[i,'UpRight'].strip()[1:-1].split(", ")]
                draw.rectangle(lowleft+upright, outline='red', width=1)
        
        img.save(saveinfo_path)
        
        print('Saving location of file:', saveinfo_path)
            
    print('Bounding boxes markup on P&ID is now complete!!!')
    gc.collect()
    
# set your working directory:
DIR = Path("D:\\ENQA\\Training\\VISTEC\\[2021] Data Science Lv2\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!

markup_PID(DIR)
