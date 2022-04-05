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
 
def get_modelspace(filename):
    
    ''' Open DXF file from input DWG file, and then setup and query the model space of text object from DXF file before extraction '''
    
    try:
        doc = ezdxf.readfile(filename)
    except IOError:
        print(f"Not a DXF file or a generic I/O error.")
        sys.exit(1)
    except ezdxf.DXFStructureError:
        print(f"Invalid or corrupted DXF file.")
        sys.exit(2)
    
    doc = ezdxf.readfile(filename)
    model_space = doc.modelspace()
        
    return model_space

def insert_df(msp):
    
    ''' Function used for collecting all information and then create the text dataframe from insert entities '''
    
    # Define entities list for verification with criteria condition
    insert_id = [insert for insert in msp.query("INSERT") if insert.dxf.name.startswith('Pipeline')]
    
    # Check the entities whether if there are any matches with the criteria condition 
    if len(insert_id) == 0:
        insert_all = pd.DataFrame(columns=['Text ID','Text Name','Text Width','Text Height','LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        pass
    else:
        inserts = msp.query("INSERT")
        insert_name = [attrib.dxf.text for insert in inserts if insert.dxf.name.startswith('Pipeline') for attrib in insert.attribs]
        insert_x = [insert.dxf.insert[0] for insert in inserts if insert.dxf.name.startswith('Pipeline')]
        insert_y = [insert.dxf.insert[1] for insert in inserts if insert.dxf.name.startswith('Pipeline')]
        insert_rot = [float(insert.dxf.rotation) for insert in inserts if insert.dxf.name.startswith('Pipeline')]
        insert_dict = {'Text ID':insert_id, 'Text Name':insert_name, 'Text X':insert_x, 'Text Y':insert_y, 'Text Rotation':insert_rot}
        insert_df = pd.DataFrame(insert_dict)
        insert_df = insert_df.assign(Type = 'F')

        # Extract the bounding box dimension into 'Ext' dataframe
        insert_idx = []
        insert_text = []
        insert_width = []
        insert_height = []
        insert_low_left_x = []
        insert_low_left_y = []
        insert_up_right_x = []
        insert_up_right_y = []

        for insert in inserts:
            if(insert.dxf.name.startswith('Pipeline')):
                for attrib in insert.attribs:
                    bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(attrib))
                    insert_idx.append(insert)
                    insert_text.append(attrib.dxf.text)
                    insert_width.append(bbox.size.x)
                    insert_height.append(bbox.size.y)
                    insert_low_left_x.append(bbox.extmin[0])
                    insert_low_left_y.append(bbox.extmin[1])
                    insert_up_right_x.append(bbox.extmax[0])
                    insert_up_right_y.append(bbox.extmax[1])

                    insert_df_ext = pd.DataFrame(list(zip(insert_idx, insert_text, insert_width, insert_height, insert_low_left_x, insert_low_left_y, insert_up_right_x, insert_up_right_y)),
                                                 columns=['Text ID','Text Name','Text Width','Text Height','LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])

        # Merge the lineList and lineExt by 'Text Name' columms
        insert_all = pd.merge(left=insert_df, right=insert_df_ext, on='Text ID', suffixes=('', '_remove'), validate='one_to_one')
        insert_all.drop([i for i in insert_all.columns if 'remove' in i], axis=1, inplace=True) # remove the duplicate columns

        # Clean the final dataframe before save file 
        for i in insert_all.index:
            # Clean the text rotation
            if (-5 < insert_all.loc[i,'Text Rotation'] < 5):
                insert_all.loc[i,'Text Rotation'] = 0
            elif (85 < insert_all.loc[i,'Text Rotation'] < 95):
                insert_all.loc[i,'Text Rotation'] = 90

            # Remove trailing text and whitespace in Text name
            if (bool(re.search(r'(?<=\s{2}).*', insert_all.loc[i,'Text Name']))):
                insert_all.loc[i,'Text Name'] = re.sub(r'(?<=\s{2}).*','', insert_all.loc[i,'Text Name']).rstrip()
            else:
                insert_all.loc[i,'Text Name'] = insert_all.loc[i,'Text Name'].rstrip()

    return insert_all
  
def text_df(msp):
    
    ''' Function used for collecting all information and then create the text dataframe from text entities '''
    
    # Define pattern for filters of text entities
    pat_full = r'\-[0-9]{6,8}\-[A-Z]' # -000000[00]-X
    pat_pref = r'\-[A-Z]{1,4}\-[0-9]{6,8}$' # -000000[00]
    pat_suff = r'^\-[A-Z][0-9]' # -X0

    # Create entities list for verification with criteria condition
    text_full_id = [t for t in msp.query("TEXT") if bool(re.search(pat_full, t.dxf.text))]
    text_pref_id = [t for t in msp.query("TEXT") if bool(re.search(pat_pref, t.dxf.text))]
    text_suff_id = [t for t in msp.query("TEXT") if bool(re.search(pat_suff, t.dxf.text))]

    # Create the text dataframe
    if (len(text_full_id) == 0) | (len(text_pref_id) == 0):
        text_all = pd.DataFrame(columns=['Text ID','Text Name','Text Width','Text Height','LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        pass
    else:
        text = msp.query("TEXT")
        # Full piping pattern dataframe
        text_full_name = [t.dxf.text for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_rot = [t.dxf.rotation for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_dict = {'Text ID':text_full_id, 'Text Name':text_full_name, 'Text X':text_full_x, 'Text Y':text_full_y, 'Text Rotation':text_full_rot}
        text_full_df = pd.DataFrame(text_full_dict).assign(Type = 'F')

        # Partial piping pattern dataframe
        text_pref_name = [t.dxf.text for t in text if bool(re.search(pat_pref, t.dxf.text))]
        text_pref_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_pref, t.dxf.text))]
        text_pref_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_pref, t.dxf.text))]
        text_pref_rot = [t.dxf.rotation for t in text if bool(re.search(pat_pref, t.dxf.text))]
        text_pref_dict = {'Text ID':text_pref_id, 'Text Name':text_pref_name, 'Text X':text_pref_x, 'Text Y':text_pref_y, 'Text Rotation':text_pref_rot}
        text_pref_df = pd.DataFrame(text_pref_dict).assign(Type = 'P')

        text_suff_name = [t.dxf.text for t in text if bool(re.search(pat_suff, t.dxf.text))]
        text_suff_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_suff, t.dxf.text))]
        text_suff_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_suff, t.dxf.text))]
        text_suff_rot = [t.dxf.rotation for t in text if bool(re.search(pat_suff, t.dxf.text))]
        text_suff_dict = {'Text ID':text_suff_id, 'Text Name':text_suff_name, 'Text X':text_suff_x, 'Text Y':text_suff_y, 'Text Rotation':text_suff_rot}
        text_suff_df = pd.DataFrame(text_suff_dict).assign(Type = 'S')

        text_part_df = pd.concat([text_pref_df, text_suff_df], axis=0, ignore_index=True, verify_integrity=True)
        text_part_df = text_part_df.assign(Distance = ( (text_part_df['Text X'])**2 + (text_part_df['Text Y'])**2 )**0.5)
        text_part_df.sort_values('Distance', ascending=[True], inplace=True)
        text_part_df.drop('Distance', axis=1, inplace=True)
        text_part_df = text_part_df.assign(Type = 'P')

        # Append the complete and partial dataframe
        text_df = pd.concat([text_full_df,text_part_df], axis=0, ignore_index=True, verify_integrity=True)

        # Extract the bounding box dimension into 'Ext' dataframe
        text_idx = []
        text_name = []
        text_width = []
        text_height = []
        text_low_left_x = []
        text_low_left_y = []
        text_up_right_x = []
        text_up_right_y = []

        for t in text:
            if(t.dxf.text in text_df['Text Name'].to_list()):
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
                text_idx.append(t)
                text_name.append(t.dxf.text)
                text_width.append(bbox.size.x)
                text_height.append(bbox.size.y)
                text_low_left_x.append(bbox.extmin[0])
                text_low_left_y.append(bbox.extmin[1])
                text_up_right_x.append(bbox.extmax[0])
                text_up_right_y.append(bbox.extmax[1])

        text_df_ext = pd.DataFrame(list(zip(text_idx, text_name, text_width, text_height, text_low_left_x, text_low_left_y, text_up_right_x, text_up_right_y)),
                                   columns=['Text ID','Text Name','Text Width','Text Height','LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])

        # Merge the lineList and lineExt by 'Text Name' columms
        text_all = pd.merge(left=text_df, right=text_df_ext, on='Text ID', suffixes=('', '_remove'), validate='one_to_one')
        text_all.drop([i for i in text_all.columns if 'remove' in i], axis=1, inplace=True) # remove the duplicate columns

        # Clean the final dataframe before save file 
        for i in text_all.index:
            # Clean the text rotation
            if (-5 < text_all.loc[i,'Text Rotation'] < 5):
                text_all.loc[i,'Text Rotation'] = 0
            elif (85 < text_all.loc[i,'Text Rotation'] < 95):
                text_all.loc[i,'Text Rotation'] = 90

            # Remove trailing text and whitespace in Text name
            if (bool(re.search(r'(?<=\s{2}).*', text_all.loc[i,'Text Name']))):
                text_all.loc[i,'Text Name'] = re.sub(r'(?<=\s{2}).*','', text_all.loc[i,'Text Name']).rstrip()
            else:
                text_all.loc[i,'Text Name'] = text_all.loc[i,'Text Name'].rstrip()
        
    return text_all
  
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
        msp = get_modelspace(filename)
        insert_all = insert_df(msp)
        text_all = text_df(msp)
        piping_df = pd.concat([insert_all,text_all], axis=0, ignore_index=True, verify_integrity=True)
        
        # Add the filename
        listname = re.split(r'\\|\.', filename)
        file_name = listname[-2]
        piping_df = piping_df.assign(Filename = file_name)
                
        # Define related parameters and check the existing save folder
        list_folders = os.listdir('.\\DXF')
        save_folder = '.\\CSV'
        trim_char = ['','DXF',file_name,'dxf']
    
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        # Save file
        if bool(len(list_folders) != 0):
            prior_folder = [folder for folder in listname if folder not in trim_char]
            prior_folder = "".join(prior_folder)
        
            if not os.path.exists(save_folder+'\\'+prior_folder): # Check the whether if existing folder is created
                os.makedirs(save_folder+'\\'+prior_folder)
            saveinfo_path = save_folder+'\\'+prior_folder+'\\'+file_name+'.csv'
        else:
            saveinfo_path = save_folder+'\\'+file_name+'.csv'
        
        piping_df.to_csv(saveinfo_path)
        print('Saving location of file:', saveinfo_path)
        
    print('\n','Complete!!!')
    gc.collect()
    
# set your working directory:
DIR = Path(".\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!
# All drawing file must be located in the 'DWG' sub-folder

info_extract_pid_uhv(DIR)
