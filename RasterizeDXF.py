import ezdxf
from ezdxf import recover
from ezdxf.addons.drawing.config import Configuration, LinePolicy
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing import matplotlib
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.properties import Properties, LayoutProperties
from ezdxf.lldxf.const import DXFAttributeError
from ezdxf.tools import fonts
import gc
import matplotlib.pyplot as plt
import os
from pathlib import Path
from PIL import Image
import regex as re
import sys

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
    
    ''' Load, and verify the DXF file, and convert all entities in the modelspace  '''
    
    # Safe file loading procedure
    try:
        doc, auditor = recover.readfile(filename)
    except IOError:
        print(f'Not a DXF file or a generic I/O error.')
        sys.exit(1)
    except ezdxf.DXFStructureError:
        print(f'Invalid or corrupted DXF file.')
        sys.exit(2)

    # DXF file can still have unrecoverable errors, but this is maybe just a problem when saving the recovered DXF file.
    if auditor.has_errors:
        auditor.print_error_report()
        raise Exception("This DXF document is damaged and can't be converted! --> ", filename)
        filename = filename =+ 1
    
    # Read file and convert all entities in the modelspace
    doc = ezdxf.readfile(filename)
    msp = doc.modelspace()
    
    # Change the color of all dxf objects in the same layer properties (ACI = 256)
    for e in msp:
        try:
            e.dxf.color = 256
        except DXFAttributeError:
            # Attribute is not present
            pass
    
    # Change the layer color to black (ACI = 7)
    for layer in doc.layers:
        layer.color = 7
        
    return msp
 
def rasterize(name: Path, filetype='png', dpi=720):
    
    ''' Convert the DXF file into raster image file type '''
    
    # Set working directory, which there is sub-folder name 'DXF' consists of *.dxf files
    os.chdir(name)
    
    print(f'DXF files have been converted into {filetype!r} files.','\n')
    print('Rasterization is proceeding...')
    
    list_files = get_file_list('DXF')
    config = Configuration.defaults()
    config = config.with_changes(lineweight_scaling=0.5, line_policy=LinePolicy.ACCURATE)
    bgcol = '#FFFFFF' # for white background: ('#FFFFFF00') to get a transparent background and a black foreground color (ACI=7)
    
    for filename in list_files:
        entities = get_modelspace(filename)
            
        # Add the filename
        listname = re.split(r'\\|\.', filename)
        file = listname[-2]
        
        # Define related parameters and check the existing save folder
        list_folders = os.listdir('.\\DXF')
        save_folder = '.\\'+filetype.upper()
        trim_char = ['','DXF',file,'dxf']
        
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        
        # Save file
        if bool(len(list_files) != 0):
            prior_folder = [folder for folder in listname if folder not in trim_char]
            prior_folder = "".join(prior_folder)
            if not os.path.exists(save_folder+'\\'+prior_folder): # Check the whether if existing folder is created
                os.makedirs(save_folder+'\\'+prior_folder)
            saveinfo_path = save_folder+'\\'+prior_folder+'\\'+file+'.'+filetype
        else:
            saveinfo_path = save_folder+'\\'+file+'.'+filetype

        matplotlib.qsave(entities, filename=saveinfo_path, bg='#FFFFFF', fg='#000000', dpi=dpi, config=config)
        
        # Adjust the gray scale color
        with Image.open(saveinfo_path) as img:
            img = img.convert('L')
            img.save(saveinfo_path)
        
        print('Saving location of file:', saveinfo_path)
    
    print('\n','Complete!!!')
    gc.collect()

# set your working directory:
DIR = Path(".\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!
# All drawing file must be located in the 'DXF' sub-folder

rasterize(name=DIR, filetype=png, dpi=720)
