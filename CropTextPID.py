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
  
def crop_text(name: Path):

  ''' Crop the text from the P&ID, and then save into the subfolder, which is the drawing filename'''

  # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
  os.chdir(name)

  print('Cropping text have been proceeding.')

  raster_path = ".\\PNG"
  icdar_path = ".\\ICDAR"
  list_raster_files = get_file_list(raster_path)
  list_icdar_files = get_file_list(icdar_path)
  list_data_files = list(zip(list_raster_files,list_icdar_files))
  list_data_files = pd.DataFrame(list_data_files, columns=['PNG','ICDAR'])

  for idx in tqdm(range(len(list_raster_files))):

      file_raster_location = list_raster_files[idx]
      file_icdar_location = list_icdar_files[idx]
      df = pd.read_csv(file_icdar_location, index_col=0)

      listname = re.split(r'\\|\.', file_raster_location)
      filename = listname[-2]
      save_cropped_folder = '.\\CropImage'
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

      print('Saving cropped text image at:', saveinfo_path)

      for row_id in range(df.shape[0]):          
          # Get the coordinate for cropping image        
          left = df.loc[row_id,'tlx']
          upper = df.loc[row_id,'tly']
          right = df.loc[row_id,'brx']
          lower = df.loc[row_id,'bry']
          textname = df.loc[row_id,'text']
          textname = re.sub('"','',textname)
          textname = re.sub('/','_',textname)

          with Image.open(file_raster_location) as img:
              # The crop method from the Image module takes four coordinates as input.
              # The right can also be represented as (left+width)
              # and lower can be represented as (upper+height
              # Here the image "img" is cropped and assigned to new variable im_crop
              img_crop = img.crop((left, upper, right, lower))
              img_crop.save(f'{saveinfo_path+textname}.png')

  print('Image cropping is now finished!!!')
  gc.collect()
    
# set your working directory:
DIR = Path("D:\\ENQA\\Training\\VISTEC\\[2021] Data Science Lv2\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!

crop_text(DIR)
