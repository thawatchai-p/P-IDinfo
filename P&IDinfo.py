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
    
    DXF_folder = 'DXF'
    
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
    OUTPUT_FOLDER = DXF_folder
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
    
    read_file = ezdxf.readfile(filename) 
    msp = read_file.modelspace()
    text = msp.query("TEXT")
    
    return text

def text_df(text):
    
    ''' Convert all text objects into dataframe and Filter out the non-piping text object '''
    
    # Convert the text object into dataframe
    all_text = [t.dxf.text for t in text]
    text_id = [t for t in text]
    text_name = [t.dxf.text for t in text]
    text_x = [t.dxf.insert[0] for t in text]
    text_y = [t.dxf.insert[1] for t in text]
    text_rot = [t.dxf.rotation for t in text]
    text_dict = {'Text ID':text_id, 'Text Name':text_name, 'Text X':text_x, 'Text Y':text_y, 'Text Rotation':text_rot}
    text_df = pd.DataFrame(text_dict)
    
    return(text_df)

def cleaned_df(text, text_df):
    
    ''' Clean the import line dataframe into the proper and neat format '''
    
    # Filter the complete line
    pat_full = r'\-[A-Z0-9]{6,8}\-[A-Z]' # -000000[00]-X
    linefull_idx = alltexttable[alltexttable['Text Name'].str.contains(pat_full)].reset_index(drop=True)
    linefull_idx = linefull_idx.assign(Type = 'F')
    linefull_idx.sort_values('Text Rotation', ascending=[True], inplace=True)
    linefull_idx = linefull_idx.reset_index(drop=True)

    # Filter the partial incomplete line pattern 1
    pat_pref_1 = r'\-[A-Z]{1,4}\-[0-9]{6,8}$' # -000000[00]
    pat_suff_1 = r'^\-[A-Z][0-9]' # -X0
    linepart_pref_1 = alltexttable[alltexttable['Text Name'].str.contains(pat_pref_1)]
    linepart_pref_1 = linepart_pref_1.assign(Type = 'P')
    linepart_suff_1 = alltexttable[alltexttable['Text Name'].str.contains(pat_suff_1)]
    linepart_suff_1 = linepart_suff_1.assign(Type = 'S')
    linepart_idx_1 = pd.concat([linepart_pref_1, linepart_suff_1], axis=0, ignore_index=True, verify_integrity=True)
    linepart_idx_1 = linepart_idx_1.assign(Length = linepart_idx_1['Text Name'].str.len())
    linepart_idx_1.sort_values('Text Rotation', ascending=[True], inplace=True)
    linepart_idx_1h = linepart_idx_1[linepart_idx_1['Text Rotation'] == 0].sort_values(['Text X','Text Y'], ascending=[True,True])
    linepart_idx_1v = linepart_idx_1[linepart_idx_1['Text Rotation'] == 90].sort_values(['Text Y','Text X'], ascending=[True,True])
    linepart_idx_1 = pd.concat([linepart_idx_1h, linepart_idx_1v], axis=0, ignore_index=True, verify_integrity=True)
    linepart_idx_1 = linepart_idx_1.assign(Type = 'P1')

    # Filter the partial incomplete line pattern 2
    pat_pref_2 = r'\-[A-Z]{1,4}\-[0-9]{6,8}\-$' # -000000[00]-
    pat_suff_2 = r'^[A-Z][0-9]' # X0
    linepart_pref_2 = alltexttable[alltexttable['Text Name'].str.contains(pat_pref_2)]
    linepart_pref_2 = linepart_pref_2.assign(Type = 'P')
    linepart_suff_2 = alltexttable[alltexttable['Text Name'].str.contains(pat_suff_2)]
    linepart_suff_2 = linepart_suff_2.assign(Type = 'S')
    linepart_idx_2 = pd.concat([linepart_pref_2, linepart_suff_2], axis=0, ignore_index=True, verify_integrity=True)
    linepart_idx_2 = linepart_idx_2.assign(Length = linepart_idx_2['Text Name'].str.len())
    linepart_idx_2.sort_values('Text Rotation', ascending=True, inplace=True)

    # Check whether if the text objects in pattern 2 are piping line text or not
    if sum(linepart_idx_2.Type == 'P') == 0:
        linepart_idx_2.drop(labels=linepart_idx_2.index, axis=0, inplace=True) 
    else :
        linepart_idx_2h = linepart_idx_2[linepart_idx_2['Text Rotation'] == 0]
        linepart_idx_2h = linepart_idx_2h[linepart_idx_2h.duplicated('Text X', keep=False)]
        linepart_idx_2h.sort_values(['Text X','Text Y'], ascending=[True,True], inplace=True)
        linepart_idx_2v = linepart_idx_2[linepart_idx_2['Text Rotation'] == 90]
        linepart_idx_2v = linepart_idx_2v[linepart_idx_2v.duplicated('Text Y', keep=False)]
        linepart_idx_2v.sort_values(['Text Y','Text X'], ascending=[True,True], inplace=True)
        linepart_idx_2 = pd.concat([linepart_idx_2h, linepart_idx_2v], axis=0, ignore_index=True, verify_integrity=True)
        linepart_idx_2 = linepart_idx_2.assign(Type = 'P2')

    linepart_idx = pd.concat([linepart_idx_1,linepart_idx_2], axis=0, ignore_index=True, verify_integrity=True)

    # Sort the partial incomplete line for both pattern
    even = linepart_idx.loc[linepart_idx.index % 2 == 0,].reset_index()
    odd = linepart_idx.loc[linepart_idx.index % 2 == 1,].reset_index()
    cond = even.Length - odd.Length

    for i in cond.index:
        if cond[i] < 0:
            even.loc[i,'index'] += 1
            odd.loc[i,'index'] -= 1

    linepart_idx = pd.concat([even,odd], axis=0, ignore_index=True, verify_integrity=True)
    linepart_idx.drop('Length', axis=1, inplace=True)
    linepart_idx.sort_values('index', ascending=True, inplace=True)
    linepart_idx.set_index('index', inplace=True)

    # Append the complete and partial dataframe
    line_list = pd.concat([linefull_idx,linepart_idx], axis=0, ignore_index=True, verify_integrity=True)

    # Extract the text box into 'listExt' dataframe
    line_idx = []
    line_name = []
    line_width = []
    line_height = []
    line_low_left_x = []
    line_low_left_y = []
    line_up_right_x = []
    line_up_right_y = []
    
    for t in text:
        if(t.dxf.text in lineList['Text Name'].to_list()):
            bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
            line_idx.append(t)
            line_name.append(t.dxf.text)
            line_width.append(bbox.size.x)
            line_height.append(bbox.size.y)
            line_low_left_x.append(bbox.extmin[0])
            line_low_left_y.append(bbox.extmin[1])
            line_up_right_x.append(bbox.extmax[0])
            line_up_right_y.append(bbox.extmax[1])

    line_ext = pd.DataFrame(list(zip(line_idx, line_name, line_width, line_height, line_low_left_x, line_low_left_y, line_up_right_x, line_up_right_y)),
                           columns=['Text ID','Text Name','Text Width','Text Height','LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])

    # Merge the lineList and lineExt by 'Text Name' columms
    line_all = pd.merge(left=line_list, right=line_ext, on='Text ID', suffixes=('', '_remove'), validate='one_to_one')
    line_all.drop([i for i in lineAll.columns if 'remove' in i], axis=1, inplace=True) # remove the duplicate columns
    
    # Clean the final database before save file 
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

def info_extract_pid(name: Path):
    
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
    
# Testing!!!
# set your working directory:
DIR = Path("D:\\ENQA\\Training\\VISTEC\\[2021] Data Science Lv2\\Use Case Project").expanduser()

# Ensure the working directory before executing!!!
# All drawing file must be located in the 'DWG' sub-folder

infoExtractPID(DIR)

# Don't forget to check the working directory before running the above command by os.getcwd()
