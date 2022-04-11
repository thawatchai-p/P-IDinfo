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

def piping_insert_full(insert_modelspace):
    
    ''' Extract the information from insert entities in the model space from DXF file '''    
    
    inserts = insert_modelspace
    
    # Define entities list for verification with criteria condition
    insert_id = [insert for insert in inserts if insert.dxf.name.startswith('Pipeline')]
    
    # Verify the text availability from insert entities, if criteria was met, then create the insert dataframe
    if len(insert_id) == 0:
        insert_all = pd.DataFrame(columns=['Text ID','Text Name','Text X','Text Y','Text Rotation','Type',
                                           'Text Width','Text Height',
                                           'LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
    else:
        insert_name = [attrib.dxf.text for insert in inserts if insert.dxf.name.startswith('Pipeline')
                       for attrib in insert.attribs]
        insert_x = [insert.dxf.insert[0] for insert in inserts if insert.dxf.name.startswith('Pipeline')]
        insert_y = [insert.dxf.insert[1] for insert in inserts if insert.dxf.name.startswith('Pipeline')]
        insert_rot = [float(insert.dxf.rotation) for insert in inserts if insert.dxf.name.startswith('Pipeline')]
        insert_dict = {'Text ID':insert_id, 'Text Name':insert_name, 'Text X':insert_x, 'Text Y':insert_y,
                       'Text Rotation':insert_rot}
        insert_df = pd.DataFrame(insert_dict)
        insert_df = insert_df.assign(Type = 'F')     
        
        # Get the extension dataframe (bounding box)
        # Extract the text box into 'listExt' dataframe
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

                    insert_ext = pd.DataFrame(list(zip(insert_idx, insert_text, insert_width, insert_height,
                                                       insert_low_left_x, insert_low_left_y,
                                                       insert_up_right_x, insert_up_right_y)),
                                                 columns=['Text ID','Text Name','Text Width','Text Height',
                                                          'LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        
        # Merge the lineList and lineExt by 'Text Name' columms
        insert_all = pd.merge(left=insert_df, right=insert_ext, on='Text ID', suffixes=('', '_remove'),
                              validate='one_to_one')
        # remove the duplicate columns
        insert_all.drop([i for i in insert_all.columns if 'remove' in i], axis=1, inplace=True)
    
    return insert_all
  
def piping_text_full(text_modelspace):
    
    ''' Extract the information from text entities, which display in the full piping pattern from DXF file '''
    
    text = text_modelspace
    
    # Define pattern for filters of text entities
    pat_full = r'.*\d\"\-[A-Z]{1,4}\-[A-Z\d]{6,8}\-[A-Z].*' # 00"-XXXX-000000[00]-X
    
    # Create entities list for verification with criteria condition
    text_full_id = [t for t in text if bool(re.search(pat_full, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_full_id) == 0:
        text_full_df = pd.DataFrame(columns=['Text ID','Text Name','Text X','Text Y','Text Rotation','Type',
                                              'Text Width','Text Height','LowerLeft X','LowerLeft Y',
                                              'UpperRight X','UpperRight Y'])      
    else:
        # Full piping pattern dataframe
        text_full_name = [t.dxf.text for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_rot = [t.dxf.rotation for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_dict = {'Text ID':text_full_id, 'Text Name':text_full_name, 'Text X':text_full_x,
                          'Text Y':text_full_y, 'Text Rotation':text_full_rot}
        text_full_df = pd.DataFrame(text_full_dict).assign(Type = 'F')
        
        # Get the extension dataframe
        # Create empty list
        text_idx = []
        text_name = []
        text_width = []
        text_height = []
        text_low_left_x = []
        text_low_left_y = []
        text_up_right_x = []
        text_up_right_y = []

        for t in text:
            if(t.dxf.text in text_full_df['Text Name'].to_list()):
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
                text_idx.append(t)
                text_name.append(t.dxf.text)
                text_width.append(bbox.size.x)
                text_height.append(bbox.size.y)
                text_low_left_x.append(bbox.extmin[0])
                text_low_left_y.append(bbox.extmin[1])
                text_up_right_x.append(bbox.extmax[0])
                text_up_right_y.append(bbox.extmax[1])

        text_full_ext = pd.DataFrame(list(zip(text_idx, text_name, text_width, text_height,
                                            text_low_left_x, text_low_left_y, text_up_right_x, text_up_right_y)),
                                   columns=['Text ID','Text Name','Text Width','Text Height',
                                        'LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_full_df = pd.merge(left=text_full_df, right=text_full_ext, on='Text ID', suffixes=('', '_remove'),
                                validate='one_to_one')
        # remove the duplicate columns
        text_full_df.drop([i for i in text_full_df.columns if 'remove' in i], axis=1, inplace=True)
    
    return text_full_df

def piping_text_part1(text_modelspace):
    
    ''' Extract the information from text entities, which display in the partial piping pattern (#1) '''
    
    text = text_modelspace
    
    # Define pattern for filters of text entities
    pat_pref1 = r'\-[A-Z]{1,4}\-[0-9]{6,8}$' # -000000[00]
    pat_suff1 = r'^\-[A-Z][0-9]' # -X0
      
    # Create entities list for verification with criteria condition
    text_pref1_id = [t for t in text if bool(re.search(pat_pref1, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_pref1_id) == 0:
        text_part1_df = pd.DataFrame(columns=['Text ID','Text Name','Text X','Text Y','Text Rotation','Type',
                                              'Text Width','Text Height','LowerLeft X','LowerLeft Y',
                                              'UpperRight X','UpperRight Y'])
        pass
    
    else:
        # Partial piping pattern dataframe
        text_pref1_name = [t.dxf.text for t in text if bool(re.search(pat_pref1, t.dxf.text))]
        
        if len(text_pref1_name) > 0:
            text_pref1_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_pref1, t.dxf.text))]
            text_pref1_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_pref1, t.dxf.text))]
            text_pref1_rot = [t.dxf.rotation for t in text if bool(re.search(pat_pref1, t.dxf.text))]
            text_pref1_dict = {'Text ID':text_pref1_id, 'Text Name':text_pref1_name, 'Text X':text_pref1_x,
                               'Text Y':text_pref1_y, 'Text Rotation':text_pref1_rot}
            text_pref1_df = pd.DataFrame(text_pref1_dict).assign(Type = 'P1')

            text_suff1_id = [t for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_name = [t.dxf.text for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_rot = [t.dxf.rotation for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_dict = {'Text ID':text_suff1_id, 'Text Name':text_suff1_name, 'Text X':text_suff1_x,
                               'Text Y':text_suff1_y, 'Text Rotation':text_suff1_rot}
            text_suff1_df = pd.DataFrame(text_suff1_dict).assign(Type = 'S1')

            text_part1_df = pd.concat([text_pref1_df, text_suff1_df], axis=0, ignore_index=True,
                                      verify_integrity=True)
            text_part1_df['Distance'] = ( (text_part1_df['Text X'])**2 + (text_part1_df['Text Y'])**2 ) **0.5 
        
        # Get the extension dataframe
        # Create empty list
        text_idx = []
        text_name = []
        text_width = []
        text_height = []
        text_low_left_x = []
        text_low_left_y = []
        text_up_right_x = []
        text_up_right_y = []

        for t in text:
            if(t.dxf.text in text_part1_df['Text Name'].to_list()):
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
                text_idx.append(t)
                text_name.append(t.dxf.text)
                text_width.append(bbox.size.x)
                text_height.append(bbox.size.y)
                text_low_left_x.append(bbox.extmin[0])
                text_low_left_y.append(bbox.extmin[1])
                text_up_right_x.append(bbox.extmax[0])
                text_up_right_y.append(bbox.extmax[1])

        text_part1_ext = pd.DataFrame(list(zip(text_idx, text_name, text_width, text_height,
                                            text_low_left_x, text_low_left_y, text_up_right_x, text_up_right_y)),
                                   columns=['Text ID','Text Name','Text Width','Text Height',
                                        'LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_part1_df = pd.merge(left=text_part1_df, right=text_part1_ext, on='Text ID', suffixes=('', '_remove'),
                                 validate='one_to_one')
        # remove the duplicate columns
        text_part1_df.drop([i for i in text_part1_df.columns if 'remove' in i], axis=1, inplace=True)
        
        # Sort the piping based on their relative postion (distance)
        text_part1_df.sort_values(['Text Rotation','Distance'], ascending=[True,True], inplace=True)
        text_part1_df.drop('Distance', axis=1, inplace=True)
        text_part1_df.reset_index(drop=True, inplace=True)
    
    return text_part1_df

def piping_text_part2(text_modelspace):
    
    ''' Extract the information from text entities, which display in the partial piping pattern (#2) '''
    
    text = text_modelspace
    
    # Define pattern for filters of text entities
    pat_pref2 = r'\-[A-Z]{1,4}\-[0-9]{6,8}\-$' # -000000[00]-
    pat_suff2 = r'^[A-Z][0-9]' # X0
      
    # Create entities list for verification with criteria condition
    text_pref2_id = [t for t in text if bool(re.search(pat_pref2, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_pref2_id) == 0:
        text_part2_df = pd.DataFrame(columns=['Text ID','Text Name','Text X','Text Y','Text Rotation','Type',
                                              'Text Width','Text Height','LowerLeft X','LowerLeft Y',
                                              'UpperRight X','UpperRight Y'])
        pass
    
    else:
        # Partial piping pattern dataframe
        text_pref2_name = [t.dxf.text for t in text if bool(re.search(pat_pref2, t.dxf.text))]
        
        if len(text_pref2_name) > 0:
            text_pref2_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_pref2, t.dxf.text))]
            text_pref2_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_pref2, t.dxf.text))]
            text_pref2_rot = [t.dxf.rotation for t in text if bool(re.search(pat_pref2, t.dxf.text))]
            text_pref2_dict = {'Text ID':text_pref2_id, 'Text Name':text_pref2_name, 'Text X':text_pref2_x,
                               'Text Y':text_pref2_y, 'Text Rotation':text_pref2_rot}
            text_pref2_df = pd.DataFrame(text_pref2_dict).assign(Type = 'P2')

            text_suff2_id = [t for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_name = [t.dxf.text for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_rot = [t.dxf.rotation for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_dict = {'Text ID':text_suff2_id, 'Text Name':text_suff2_name, 'Text X':text_suff2_x,
                               'Text Y':text_suff2_y, 'Text Rotation':text_suff2_rot}
            text_suff2_df = pd.DataFrame(text_suff2_dict).assign(Type = 'S2')

            text_part2_df = pd.concat([text_pref2_df, text_suff2_df], axis=0, ignore_index=True,
                                      verify_integrity=True)
            text_part2_df['Distance'] = ( (text_part2_df['Text X'])**2 + (text_part2_df['Text Y'])**2 ) **0.5 
        
        # Get the extension dataframe
        # Create empty list
        text_idx = []
        text_name = []
        text_width = []
        text_height = []
        text_low_left_x = []
        text_low_left_y = []
        text_up_right_x = []
        text_up_right_y = []

        for t in text:
            if(t.dxf.text in text_part2_df['Text Name'].to_list()):
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
                text_idx.append(t)
                text_name.append(t.dxf.text)
                text_width.append(bbox.size.x)
                text_height.append(bbox.size.y)
                text_low_left_x.append(bbox.extmin[0])
                text_low_left_y.append(bbox.extmin[1])
                text_up_right_x.append(bbox.extmax[0])
                text_up_right_y.append(bbox.extmax[1])

        text_part2_ext = pd.DataFrame(list(zip(text_idx, text_name, text_width, text_height,
                                            text_low_left_x, text_low_left_y, text_up_right_x, text_up_right_y)),
                                   columns=['Text ID','Text Name','Text Width','Text Height',
                                        'LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_part2_df = pd.merge(left=text_part2_df, right=text_part2_ext, on='Text ID', suffixes=('', '_remove'),
                                 validate='one_to_one')
        # remove the duplicate columns
        text_part2_df.drop([i for i in text_part2_df.columns if 'remove' in i], axis=1, inplace=True)
        
        # Sort the piping based on their relative postion (distance)
        text_part2_df.sort_values(['Text Rotation','Distance'], ascending=[True,True], inplace=True)
        text_part2_df.drop('Distance', axis=1, inplace=True)
        text_part2_df.reset_index(drop=True, inplace=True)
        
        # Check and verify whether if there is number of prefix piping != suffix row, and fix it, if any
        if text_pref2_df.shape[0] == text_suff2_df.shape[0]:
            pass
        else:   
            piping_clean_idx = []

            for i in text_part2_df.index:
                if (len(text_part2_df.loc[i,'Text Name']) > 3) & (i % 2 == 0):
                    couple_rows = [i, i+1]
                    piping_clean_idx += couple_rows

            text_part2_df = text_part2_df.loc[piping_clean_idx,:]
    
    return text_part2_df

def piping_text_part3(text_modelspace):
    
    ''' Extract the information from text entities, which display in the partial piping pattern (#3) '''
    
    text = text_modelspace
    
    # Define pattern for filters of text entities
    pat_pref3 = r'\-[A-Z]{1,4}\-$' # 0"-XXXX-
    pat_suff3 = r'^[0-9]{6,8}\-[A-Z][0-9]' # 000000[00]-
      
    # Create entities list for verification with criteria condition
    text_pref3_id = [t for t in text if bool(re.search(pat_pref3, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_pref3_id) == 0:
        text_part3_df = pd.DataFrame(columns=['Text ID','Text Name','Text X','Text Y','Text Rotation','Type',
                                              'Text Width','Text Height','LowerLeft X','LowerLeft Y',
                                              'UpperRight X','UpperRight Y'])
        pass
    
    else:
        # Partial piping pattern dataframe
        text_pref3_name = [t.dxf.text for t in text if bool(re.search(pat_pref3, t.dxf.text))]
        
        if len(text_pref3_name) > 0:
            text_pref3_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_pref3, t.dxf.text))]
            text_pref3_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_pref3, t.dxf.text))]
            text_pref3_rot = [t.dxf.rotation for t in text if bool(re.search(pat_pref3, t.dxf.text))]
            text_pref3_dict = {'Text ID':text_pref3_id, 'Text Name':text_pref3_name, 'Text X':text_pref3_x,
                               'Text Y':text_pref3_y, 'Text Rotation':text_pref3_rot}
            text_pref3_df = pd.DataFrame(text_pref3_dict).assign(Type = 'P3')
            text_pref3_df['Distance'] = ( (text_pref3_df['Text X'])**2 + (text_pref3_df['Text Y'])**2 )**0.5
            text_pref3_df.sort_values(['Text Rotation','Distance'], ascending=[True,True], inplace=True)
            
            text_suff3_id = [t for t in text if bool(re.search(pat_suff3, t.dxf.text))]
            text_suff3_name = [t.dxf.text for t in text if bool(re.search(pat_suff3, t.dxf.text))]
            text_suff3_x = [t.dxf.insert[0] for t in text if bool(re.search(pat_suff3, t.dxf.text))]
            text_suff3_y = [t.dxf.insert[1] for t in text if bool(re.search(pat_suff3, t.dxf.text))]
            text_suff3_rot = [t.dxf.rotation for t in text if bool(re.search(pat_suff3, t.dxf.text))]
            text_suff3_dict = {'Text ID':text_suff3_id, 'Text Name':text_suff3_name, 'Text X':text_suff3_x,
                               'Text Y':text_suff3_y, 'Text Rotation':text_suff3_rot}
            text_suff3_df = pd.DataFrame(text_suff3_dict).assign(Type = 'S3')
            text_suff3_df['Distance'] = ( (text_suff3_df['Text X'])**2 + (text_suff3_df['Text Y'])**2 )**0.5
            text_suff3_df.sort_values(['Text Rotation','Distance'], ascending=[True,True], inplace=True)
            
            text_part3_df = pd.concat([text_pref3_df, text_suff3_df], axis=0, ignore_index=True,
                                      verify_integrity=True)
            text_part3_df.sort_index(axis=0, ascending=True, inplace=True)
            
        # Get the extension dataframe
        # Create empty list
        text_idx = []
        text_name = []
        text_width = []
        text_height = []
        text_low_left_x = []
        text_low_left_y = []
        text_up_right_x = []
        text_up_right_y = []

        for t in text:
            if(t.dxf.text in text_part3_df['Text Name'].to_list()):
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
                text_idx.append(t)
                text_name.append(t.dxf.text)
                text_width.append(bbox.size.x)
                text_height.append(bbox.size.y)
                text_low_left_x.append(bbox.extmin[0])
                text_low_left_y.append(bbox.extmin[1])
                text_up_right_x.append(bbox.extmax[0])
                text_up_right_y.append(bbox.extmax[1])

        text_part3_ext = pd.DataFrame(list(zip(text_idx, text_name, text_width, text_height,
                                            text_low_left_x, text_low_left_y, text_up_right_x, text_up_right_y)),
                                   columns=['Text ID','Text Name','Text Width','Text Height',
                                        'LowerLeft X','LowerLeft Y','UpperRight X','UpperRight Y'])
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_part3_df = pd.merge(left=text_part3_df, right=text_part3_ext, on='Text ID', suffixes=('', '_remove'),
                                 validate='one_to_one')
         # remove the duplicate columns
        text_part3_df.drop([i for i in text_part3_df.columns if 'remove' in i], axis=1, inplace=True)
        
        # Sort the piping based on their relative postion (distance)
        prefix3 = text_part3_df.loc[text_part3_df.Type == 'P3'].reset_index()
        pref3_idx = [prefix3.index*2]
        prefix3.set_index(pref3_idx, drop=True, verify_integrity=True, inplace=True)
        prefix3.drop('index', axis=1, inplace=True)
        
        suffix3 = text_part3_df.loc[text_part3_df.Type == 'S3'].reset_index()
        suff3_idx = [2*suffix3.index + 1]
        suffix3.set_index(suff3_idx, drop=True, verify_integrity=True, inplace=True)
        suffix3.drop('index', axis=1, inplace=True)
        
        text_part3_df = pd.concat([prefix3,suffix3], axis=0, ignore_index=False, verify_integrity=True)
        text_part3_df.sort_index(axis=0, ascending=True, inplace=True)
        text_part3_df.drop('Distance', axis=1, inplace=True)
    
    return text_part3_df

def text_rotation_cleansing(text_df):
        
    ''' Correct the value of text rotation column in text entities dataframe '''
    
    # Checking whether if there is any abnormal text rotation in the horizontal orientation (0')
    if text_df[(text_df['Text Rotation'] != 0) &
               (text_df['Text Rotation'] > -5) &
               (text_df['Text Rotation'] < 5)].shape[0] == 0:
        for i in text_df.index:
            text_df.loc[i,'Text Rotation'] = 0
    
    # Checking whether if there is any abnormal text rotation in the vertical orientation (90')        
    elif text_df[(text_df['Text Rotation'] != 90) &
                 (text_df['Text Rotation'] > -5) &
                 (text_df['Text Rotation'] < 95)].shape[0] == 0:
        for i in text_df.index:
            text_df.loc[i,'Text Rotation'] = 90
    
    return text_df

def text_name_cleansing(text_df):
    
    ''' Correct the typo (trailing text) and white space in the text entities dataframe '''
    
    # Remove irrelant prefix text and whitespace in 'Text Name' column
    r_pref = re.compile(r'.*:')
    if sum(text_df['Text Name'].apply(lambda x: bool(r_pref.match(x)))) > 0:
        for i in text_df.index:
            text_df.loc[i,'Text Name'] = re.sub(r_pref, '', text_df.loc[i,'Text Name']).lstrip()
    
    # Remove trailing text and whitespace in 'Text Name' column
    r_suff = re.compile(r'(?=\s{2}).*')
    if sum(text_df['Text Name'].apply(lambda x: bool(r_suff.match(x)))) > 0:
        for i in text_df.index:
            text_df.loc[i,'Text Name'] = re.sub(r_suff, '', text_df.loc[i,'Text Name']).rstrip()
    
    return text_df
  
def info_extract_pid_uhv(name: Path):
    
    ''' Extract the information from the DWG file, and then save the relevant information into *.csv file '''
    
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
        # Create and query the model space
        model_space = get_modelspace(filename)
        insert_modelspace = model_space.query('INSERT')
        text_modelspace = model_space.query('TEXT')
        
        # Create the component dataframes of each piping text pattern
        insert_df = piping_insert_full(insert_modelspace)
        text_full_df = piping_text_full(text_modelspace)
        text_part1_df = piping_text_part1(text_modelspace)
        text_part2_df = piping_text_part2(text_modelspace)
        text_part3_df = piping_text_part3(text_modelspace)
        
        # Append all of component dataframes
        piping_df = pd.concat([insert_df,text_full_df,text_part1_df,text_part2_df,text_part3_df], axis=0,
                              ignore_index=True, verify_integrity=True)
        
        # Add the filename
        listname = re.split(r'\\|\.', filename)
        file_name = listname[-2]
        piping_df = piping_df.assign(Filename = file_name)
        
        # Clean the dataframe
        piping_df = text_rotation_cleansing(piping_df)
        piping_df = text_name_cleansing(piping_df)
                
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
            
            # Check the whether if existing folder is created        
            if not os.path.exists(save_folder+'\\'+prior_folder): 
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
