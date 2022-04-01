import importlib.util
import sys

# For illustrative purposes.
name = 'ezdxf'

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
    !pip3 install ezdxf[draw]

import ezdxf
from ezdxf import bbox
from ezdxf.addons import text2path
import gc
import matplotlib
import os
import pandas as pd
from pathlib import Path
import regex as re
import subprocess
import sys

# Check whether if the output folder is create
def dwg_to_dxf():
    
    ''' Convert the DWG file into DXF file format '''
    
    dxf_folder = 'DXF'
    
    if not os.path.exists(DXF_folder):
        os.makedirs(DXF_folder)
    
    # Please install Teigha File Converter by copy and paste the as following link in URL:
    # https://teigha-file-converter.software.informer.com/
    # Please check the working directory (os.getcwd()) to ensure the correct working directory
    
    # Parameters Setup:
    # TEIGHA_PATH: Location of .exe file
    # Input folder: Location of input folder
    # Output folder: Location of output folder
    # Output version: ACAD9, ACAD10, ACAD12, ACAD14, ACAD2000, ACAD2004, ACAD2007, ACAD20010, ACAD2013, ACAD2018
    # Output file type: DWG, DXF, DXB
    # Recurse Input Folder: 0, 1
    # Audit each file: 0, 1
    # (Optional) Input files filter: *.DWG, *.DXF

    TEIGHA_PATH = "C:/Program Files (x86)/ODA/Teigha File Converter 4.3.2/TeighaFileConverter.exe"
    INPUT_FOLDER = "./DWG" # all drawing file must locate in this folder
    OUTPUT_FOLDER = dxf_folder
    OUTVER = "ACAD2018"
    OUTFORMAT = "DXF"
    RECURSIVE = "1"
    AUDIT = "1"
    INPUTFILTER = "*.DWG"
    
    # Command to run
    cmd = [TEIGHA_PATH, INPUT_FOLDER, OUTPUT_FOLDER, OUTVER, OUTFORMAT, RECURSIVE, AUDIT, INPUTFILTER]
    
    # Run
    subprocess.run(cmd, shell=True)
    
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
 
def get_text_entities(filename):
    
    ''' Open DXF file from input DWG file, and then setup and query the model space of text object from DXF file before extraction '''
    
    try:
        doc = ezdxf.readfile(filename)
    except IOError:
        print(f"Not a DXF file or a generic I/O error.")
        sys.exit(1)
    except ezdxf.DXFStructureError:
        print(f"Invalid or corrupted DXF file.")
        sys.exit(2)
    
    doc = ezdxf.readfile(sample_file)
    model_space = doc.modelspace()
    inserts = model_space.query("INSERT")
    
    return insert

def text_df(insert):
    
    ''' Convert all text objects into dataframe and Filter out the non-piping text object '''
    
    # Convert the text object into dataframe
    text_id = [insert for insert in inserts if insert.dxf.name.startswith('Pipeline')]
    text_name = [attrib.dxf.text for insert in inserts if insert.dxf.name.startswith('Pipeline') for attrib in insert.attribs]
    text_x = [insert.dxf.insert[0] for insert in inserts if insert.dxf.name.startswith('Pipeline')]
    text_y = [insert.dxf.insert[1] for insert in inserts if insert.dxf.name.startswith('Pipeline')]
    text_rot = [float(insert.dxf.rotation) for insert in inserts if insert.dxf.name.startswith('Pipeline')]
    text_dict = {'Text ID':text_id, 'Text Name':text_name, 'Text X':text_x, 'Text Y':text_y, 'Text Rotation':text_rot}
    text_df = pd.DataFrame(text_dict)
    text_df = text_df.assign(Type = 'F')
    
    return(text_df)
  
def cleaned_df(insert, text_df):

    ''' Clean the import line dataframe into the proper and neat format '''

    # Extract the text box into 'list_ext' dataframe
    line_idx = []
    line_name = []
    line_width = []
    line_height = []
    line_low_left_x = []
    line_low_left_y = []
    line_up_right_x = []
    line_up_right_y = []

    for insert in inserts:
        if(insert.dxf.name.startswith('Pipeline')):
            for attrib in insert.attribs:
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(attrib))
                line_idx.append(insert)
                line_name.append(attrib.dxf.text)
                line_width.append(bbox.size.x)
                line_height.append(bbox.size.y)
                line_low_left_x.append(bbox.extmin[0])
                line_low_left_y.append(bbox.extmin[1])
                line_up_right_x.append(bbox.extmax[0])
                line_up_right_y.append(bbox.extmax[1])

    line_ext = pd.DataFrame(list(zip(line_idx, line_name, line_width, line_height, line_low_left_x, line_low_left_y, line_up_right_x, line_up_right_y)),
                            columns=['Text ID','Text Name','Text Width','Text Height','LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])

    # Add the filename
    listname = re.split(r'\\|\.', sample_file)
    filename = listname[-2]
    line_ext = line_ext.assign(Filename = filename)

    # Merge the lineList and lineExt by 'Text Name' columms
    line_all = pd.merge(left=text_df, right=line_ext, on='Text ID', suffixes=('', '_remove'), validate='one_to_one')
    line_all.drop([i for i in line_all.columns if 'remove' in i], axis=1, inplace=True) # remove the duplicate columns

    # Clean the final dataframe before save file 
    for i in line_all.index:
        # Clean the text rotation
        if (-5 < line_all.loc[i,'Text Rotation'] < 5):
            line_all.loc[i,'Text Rotation'] = 0
        elif (85 < line_all.loc[i,'Text Rotation'] < 95):
            line_all.loc[i,'Text Rotation'] = 90

        # Remove trailing text and whitespace in Text name
        if (bool(re.search(r'(?<=\s{2}).*', line_all.loc[i,'Text Name']))):
            line_all.loc[i,'Text Name'] = re.sub(r'(?<=\s{2}).*','', line_all.loc[i,'Text Name']).rstrip()
        else:
            line_all.loc[i,'Text Name'] = line_all.loc[i,'Text Name'].rstrip()

    return line_all
  
def info_extract_pid_uhv(name: Path):
    
    ''' Extract the information from the DWG file in the folder, and then save the relevant information into *.csv file '''
    
    # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
    os.chdir(name)
        
    # Check whether if dxf files have been already converted into .DXF files
    print('Have all converted files located in the "DXF" Folder (y/n): ')
    decision = input()
    
    if decision == 'n':
        dwg_to_dxf()
    
    print('DWG files have been converted into DXF files.','\n')
    print('Information extraction is proceeding.')
    
    list_files = get_file_list('DXF')
     
    for filename in list_files:
        text = get_text_entities(filename)
        all_line_df = text_df(text)
        clean_df = cleaned_df(text, all_line_df)
        
        # Add the filename
        listname = re.split(r'\\|\.', filename)
        file = listname[-2]
        clean_df = clean_df.assign(Filename = file)
        
        # Define related parameters and check the existing save folder
        list_folders = os.listdir('.\\DXF')
        save_folder = '.\\CSV_Output'
        trim_char = ['','DXF',file,'dxf']
    
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        # Save file
        if bool(len(list_folders) != 0):
            prior_folder = [folder for folder in listname if folder not in trim_char]
            prior_folder = "".join(prior_folder)
        
            if not os.path.exists(save_folder+'\\'+prior_folder): # Check the whether if existing folder is created
                os.makedirs(save_folder+'\\'+prior_folder)
            saveinfo_path = save_folder+'\\'+prior_folder+'\\'+file+'.csv'
        else:
            saveinfo_path = save_folder+'\\'+file+'.csv'
        
        clean_df.to_csv(saveinfo_path)
        print('Saving location of file:', saveinfo_path)
        
    print('\n','Complete!!!')
    gc.collect()
    
# set your working directory:
DIR = Path(".\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!
# All drawing file must be located in the 'DWG' sub-folder

info_extract_pid_uhv(DIR)
