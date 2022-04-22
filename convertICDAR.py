import gc
import pandas as pd
import os
from pathlib import Path
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
  
def convert_ICDAR_format(name: Path):

  ''' Convert, clean and tidy the .csv dataframe into ICDAR format'''

  # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
  os.chdir(name)

  print('CSV files have been converted into ICDAR format.','\n')
  print('Conversion is proceeding...')

  list_files = get_file_list('CSV')

  for idx in tqdm( range(len(list_files)) ):

      filename_path = list_files[idx]

      # Get the data file and remove unnecessary columns
      df = pd.read_csv(filename_path, index_col=0)

      # Get the filename
      listname = re.split(r'\\|\.', filename_path)
      filename = listname[-2]

      # Define related parameters and check the existing save folder
      save_icdar_folder = '.\\ICDAR'
      trim_char = ['','CSV',filename,'csv']

      if not os.path.exists(save_icdar_folder):
          os.makedirs(save_icdar_folder)

      # Save file
      if bool(len(list_files) != 0):

          prior_folder = [folder for folder in listname if folder not in trim_char]
          prior_folder = "".join(prior_folder)
          if not os.path.exists(save_icdar_folder+'\\'+prior_folder): # Check the whether if existing folder is created
              os.makedirs(save_icdar_folder+'\\'+prior_folder)
          saveinfo_path = save_icdar_folder+'\\'+prior_folder+'\\'+filename+'.csv'

      else:
          saveinfo_path = save_csv_folder+'\\'+filename+'.csv'

      # Verify wether if there is any row in the dataframe
      if df.shape[0] == 0:
          df = pd.DataFrame(columns=['tlx', 'tly', 'trx', 'try', 'brx', 'bry', 'blx', 'bly', 'text'])

      else:            
          df = df.drop(['ID','Rotation','Type','Pattern','Filename'], axis=1)
          # Convert the 2-rasterized coordinates into 4 locations (8 positions) of bounding boxes 
          lowleft = pd.Series([re.sub(r'\(|\)','',df.loc[i,'LowLeft']) for i in df.index]).str.split(',')
          blx = [float(x) for x,y in lowleft] # 1
          bly = [float(y) for x,y in lowleft] # 2

          upright = pd.Series([re.sub(r'\(|\)','',df.loc[i,'UpRight']) for i in df.index]).str.split(',')
          trx = [float(x) for x,y in upright] # 3
          _try = [float(y) for x,y in upright] # 4

          tlx = blx
          tly = _try
          brx = trx
          bry = bly

          # Add the 8 positions into dataframe and remove unnecessary columns
          df = df.assign(tlx=tlx, tly=tly, trx=trx, _try=_try, brx=brx, bry=bry,blx=blx, bly=bly)
          df = df.drop(['LowLeft','UpRight'], axis=1)

          # Sort the columns order
          cols = ['tlx', 'tly', 'trx', '_try', 'brx', 'bry', 'blx', 'bly', 'Name']
          df = df[cols]

          # Change the column name which violate the rule of setup variable name (_try)
          df.columns = ['tlx', 'tly', 'trx', 'try', 'brx', 'bry', 'blx', 'bly', 'text']

      df.to_csv(saveinfo_path)

      print('Saving location of file:', saveinfo_path)

  print('\n','Complete!!!')
  gc.collect()
    
# set your working directory:
DIR = Path("D:\\ENQA\\Training\\VISTEC\\[2021] Data Science Lv2\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!

convert_ICDAR_format(DIR)
