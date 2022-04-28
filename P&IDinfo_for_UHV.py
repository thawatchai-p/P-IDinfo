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

def frame_dimension(model_space):
    
    ''' Calculate the drawing frame dimension (width x height) '''
    
    frame_name_list = ['CCP_A1_Template FOR PID-20180103','CCP_A1_Template FOR PID','CCP_A1_Template FOR PID-REV.0',
                       'CCP_A1_Template FOR UDD','FW TIT','Title Block-UHV-01','gtdf','A$C46B42D60']
    
    if len( [i for i in model_space.query('3DFACE')] ) != 0:
    
        face3d = model_space.query('3DFACE')

        frame_idx = []
        frame_width = []
        frame_height = []
        frame_originate = []

        for e in face3d:
            frame_idx.append(e)
            frame_width.append( round(abs(e.dxf.vtx2[0] - e.dxf.vtx0[0]),4) )
            frame_height.append( round(abs(e.dxf.vtx2[1] - e.dxf.vtx0[1]),4) )
            originate = min(e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx2, e.dxf.vtx3)
            frame_originate.append( (round(originate[0],4),round(originate[1],4)) )

        face3d_df = pd.DataFrame(list(zip(frame_idx, frame_width, frame_height, frame_originate)),
                                 columns=['Frame Index','Frame Width','Frame Height','Frame Originate'])

        face3d_df['Distance'] = ( (face3d_df['Frame Width'])**2 + (face3d_df['Frame Height'])**2)**0.5
        idx = face3d_df['Distance'].argmax()
        frame_dim = face3d_df.iloc[idx,1:4].to_dict()
        pass
    
    elif len( [insert for insert in model_space.query('INSERT') if (insert.dxf.name in frame_name_list)] ) != 0:
        
        inserts = model_space.query('INSERT')
        cache = bbox.Cache()
        framebbox = BoundingBox2d( bbox.extents(inserts, cache=cache) )
        
        frame_idx = [insert.dxf.handle for insert in inserts if (insert.dxf.name in frame_name_list)]
        frame_width = [ round( abs(framebbox.extmax[0] - framebbox.extmin[0]), 4) ]
        frame_height = [ round( abs(framebbox.extmax[1] - framebbox.extmin[1]), 4) ]
        frame_originate = [ (round(framebbox.extmin[0],4), round(framebbox.extmin[1],4)) 
                           for insert in inserts if (insert.dxf.name in frame_name_list) ]
        
        frame_df = pd.DataFrame(list(zip(frame_idx, frame_width, frame_height, frame_originate)), 
                                columns=['Frame Index','Frame Width','Frame Height','Frame Originate'])
        
        frame_df['Distance'] = ( (frame_df['Frame Width'])**2 + (frame_df['Frame Height'])**2)**0.5
        idx = frame_df['Distance'].argmax()
        frame_dim = frame_df.iloc[idx,1:4].to_dict()
        
    else:
        lwpolylines = model_space.query('LWPOLYLINE')
        
        lwpolyline_idx = []
        lwpolyline_width = []
        lwpolyline_height = []
        lwpolyline_originate = []

        for e in lwpolylines:
            if (e.dxf.flags == 1) & (e.__len__() == 4):
                lwpolyline_idx.append(e.dxf.handle)
                lwpolyline_width.append( round(abs(e.get_points(format='xy')[3][0] - e.get_points(format='xy')[1][0]),4) )
                lwpolyline_height.append( round(abs(e.get_points(format='xy')[3][1] - e.get_points(format='xy')[1][1]),4) )
                originate = list( min(e.get_points(format='xy')[0], e.get_points(format='xy')[1],
                                      e.get_points(format='xy')[2], e.get_points(format='xy')[3]) )
                lwpolyline_originate.append( (round(originate[0],4),round(originate[1],4)) )

        lwpolyline_df = pd.DataFrame(list(zip(lwpolyline_idx, lwpolyline_width, lwpolyline_height, lwpolyline_originate)),
                                         columns=['Frame Index','Frame Width','Frame Height','Frame Originate'])

        lwpolyline_df['Distance'] = ( (lwpolyline_df['Frame Width'])**2 + (lwpolyline_df['Frame Height'])**2)**0.5
        lwpolyline_idx = lwpolyline_df['Distance'].argmax()
        lwpolyline_dim = pd.Series(lwpolyline_df.iloc[lwpolyline_idx,1:4])

        lines = model_space.query('LINE')
        
        line_idx = []
        line_starts_x = []
        line_starts_y = []
        line_ends_x = []
        line_ends_y = []

        for line in lines:
            starts = line.dxf.start
            ends = line.dxf.end
            if (ends[1] - starts[1]) == 0:
                line_idx.append(line.dxf.handle)
                line_starts_x.append(starts[0])
                line_starts_y.append(starts[1])
                line_ends_x.append(ends[0])
                line_ends_y.append(ends[1])

        line_df = pd.DataFrame(list(zip(line_idx, line_starts_x, line_starts_y, line_ends_x, line_ends_y)),
                                         columns=['Frame Index','Frame Sx','Frame Sy','Frame Ex','Frame Ey'])

        lowleft = line_df.sort_values(['Frame Sx','Frame Sy'], ascending=[True, True])[0:1].squeeze()[1:3]
        lowleft = [round(s, 4) for s in lowleft]
        upright = line_df.sort_values(['Frame Ex','Frame Ey'], ascending=[False, False])[0:1].squeeze()[3:]
        upright = [round(s, 4) for s in upright]

        line_dict = {'Frame Width': round(upright[0] - lowleft[0], 4),
                     'Frame Height': round(upright[1] - lowleft[1], 4),
                     'Frame Originate': tuple(lowleft)}

        line_dim = pd.Series(line_dict)

        frame_dim = pd.DataFrame([lwpolyline_dim, line_dim]).sort_values('Frame Width', ascending=False).reset_index(drop=True)
        frame_dim = frame_dim.iloc[0].to_dict()

    return frame_dim

def text_rotation_cleansing(text_df):
        
    ''' Correct the value of text rotation column in text entities dataframe '''
    
    idx_h = (text_df['Rotation'] != 0) & ((text_df['Rotation'] > -10) | (text_df['Rotation'] > 350)) & (text_df['Rotation'] < 10)
    idx_v = (text_df['Rotation'] != 90) & (text_df['Rotation'] > 80) & (text_df['Rotation'] < 100)
    
    # Checking whether if there is any abnormal text rotation in the horizontal orientation (0')
    for h in text_df[idx_h].index:  
        if text_df.loc[idx_h].shape[0] != 0:
            text_df.loc[h,'Rotation'] = round(0.0,-1)
    
    # Checking whether if there is any abnormal text rotation in the vertical orientation (90')        
    for v in text_df[idx_v].index:
        if text_df.loc[idx_v].shape[0] != 0:
            text_df.loc[v,'Rotation'] = round(90.0,-1)
            
    return text_df

def round_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

def round_down(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

def entities_dim_transform_ratio(frame_dim, entities_df):
    
    ''' Transform the coordinate in the dxf file in to ratio value before convert to the rasterized coordinate '''
            
    entities_df_ratio = entities_df.copy()

    lowleft_x = [ (lowleft_x - frame_dim['Frame Originate'][0]) / frame_dim['Frame Width'] for lowleft_x, lowleft_y in entities_df_ratio['LowLeft']]
    lowleft_y = [ (lowleft_y - frame_dim['Frame Originate'][1]) / frame_dim['Frame Height'] for lowleft_x, lowleft_y in entities_df_ratio['LowLeft']]
    upright_x = [ (upright_x - frame_dim['Frame Originate'][0]) / frame_dim['Frame Width'] for upright_x, upright_y in entities_df_ratio['UpRight']]
    upright_y = [ (upright_y - frame_dim['Frame Originate'][1]) / frame_dim['Frame Height'] for upright_x, upright_y in entities_df_ratio['UpRight']]

    entities_df_ratio['LowLeft'] = tuple(zip(lowleft_x, lowleft_y))
    entities_df_ratio['UpRight'] = tuple(zip(upright_x, upright_y))
    
    return entities_df_ratio

def translation_matrix(x: float, y: float) -> np.ndarray:
    m = np.eye(3)
    m[0, 2] = x
    m[1, 2] = y
    return m

def scale_matrix(x: float, y: float) -> np.ndarray:
    return np.diag((x, y, 1))

def get_wcs_to_image_transform(ax: plt.Axes, image_size: Tuple[int, int]) -> np.ndarray:
    x1, x2 = ax.get_xlim()
    y1, y2 = ax.get_ylim()
    data_width, data_height = x2 - x1, y2 - y1
    image_width, image_height = image_size
    # +1 to counteract the effect of the pixels being flipped in y
    return (translation_matrix(0, image_height + 1) @
            scale_matrix(image_width / data_width, -image_height / data_height) @
            translation_matrix(-x1, -y1))

def transform_point(x:float, y: float, m: np.ndarray) -> Tuple[float, float]:
    return tuple((m @ [x, y, 1])[:2].tolist())

def entities_dim_transform_raster(raster_file, entities_df_scale):
    
    ''' Transform the scale coordinate ratio from dxf file into coordinate for raster file '''
    
    # Calculate the transform matrix for coordinate conversion from dxf to raster file
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    img = Image.open(raster_file)
    m = get_wcs_to_image_transform(ax, img.size)
    plt.close()
    
    entities_df_raster = entities_df_scale.copy()
    lowleft = [[x,y] for x,y in entities_df_raster['LowLeft']]
    upright = [[x,y] for x,y in entities_df_raster['UpRight']]
    
    for i in entities_df_raster.index:  
        lowleft[i] = transform_point(lowleft[i][0], lowleft[i][1], m)
        upright[i] = transform_point(upright[i][0], upright[i][1], m)
    
    entities_df_raster['LowLeft'] = tuple(lowleft)
    entities_df_raster['UpRight'] = tuple(upright)
    
    entities_df_raster['LowLeft'] = tuple([np.round(each_arr, decimals=3) for each_arr in entities_df_raster['LowLeft']])
    entities_df_raster['UpRight'] = tuple([np.round(each_arr, decimals=3) for each_arr in entities_df_raster['UpRight']])
    
    return entities_df_raster

def piping_insert_full(modelspace):
    
    ''' Extract the bounding box coordinate ratio from insert entities in the model space from DXF file '''    
    
    inserts = modelspace.query('INSERT')
    frame_dim = frame_dimension(modelspace)
    prefixes = ['Pipeline', 'LINE NO']
    
    # Define entities list for verification with criteria condition
    insert_id = [insert for insert in inserts if insert.dxf.name.startswith(tuple(prefixes))]
    
    # Verify the text availability from insert entities, if criteria was met, then create the insert dataframe
    if len(insert_id) == 0:
        insert_ratio = pd.DataFrame(columns=['ID','Name','Rotation','Type','Pattern','LowLeft','UpRight'])
    else:
        insert_name = [attrib.dxf.text for insert in inserts if insert.dxf.name.startswith(tuple(prefixes)) for attrib in insert.attribs]
        insert_name = [name for name in insert_name if name != ' ']
        insert_x = [round(insert.dxf.insert[0],3) for insert in inserts if insert.dxf.name.startswith(tuple(prefixes))]
        insert_y = [round(insert.dxf.insert[1],3) for insert in inserts if insert.dxf.name.startswith(tuple(prefixes))]
        insert_rot = [float(insert.dxf.rotation) for insert in inserts if insert.dxf.name.startswith(tuple(prefixes))]
        insert_scale_x = [float(insert.dxf.xscale) for insert in inserts if insert.dxf.name.startswith(tuple(prefixes))]
        insert_scale_y = [float(insert.dxf.yscale) for insert in inserts if insert.dxf.name.startswith(tuple(prefixes))]
        insert_dict = {'ID':insert_id, 'Name':insert_name, 'Text X':insert_x, 'Text Y':insert_y, 'Rotation':insert_rot,
                      'Text Scale X':insert_scale_x, 'Text Scale Y':insert_scale_y}
        insert_df = pd.DataFrame(insert_dict)
        insert_df = insert_df.assign(Type = 'I', Pattern = 'F')
        
        # Clean the text rotation column
        insert_df = text_rotation_cleansing(insert_df)
        
        # Check the consistency of text scaling values in the dataframe       
        if (len(insert_df['Text Scale X'].value_counts().index) == 1) & (len(insert_df['Text Scale Y'].value_counts().index)) == 1:
            print('There are multiple scale values, please check the drawing!!!')
            
        scale_x = 0.75
        scale_y = 0.75
        
        # Get the bounding box data from dxf file
        insert_idx = []
        insert_text = []
        insert_rot = []
        insert_width = []
        insert_height = []

        for insert in inserts:
            if(insert.dxf.name.startswith(tuple(prefixes))):
                for attrib in insert.attribs:
                    if attrib.dxf.text != ' ':
                        bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(attrib))
                        insert_idx.append(insert)
                        insert_text.append(attrib.dxf.text)
                        insert_rot.append(insert.dxf.rotation)

                        if insert.dxf.rotation == 0: # Horizontal orientation
                            insert_width.append( (bbox.size.x/scale_x) - 3 )
                            insert_height.append( (bbox.size.y/scale_y) )
                        else : # Vertical orientation
                            insert_width.append( (bbox.size.x/scale_x) )
                            insert_height.append( (bbox.size.y/scale_y) - 2 )

        insert_ext = pd.DataFrame(list(zip(insert_idx, insert_text, insert_rot, insert_width, insert_height)),
                                  columns=['ID','Name','Rotation','Text Width','Text Height'])
        
        # Merge the dataframe (df and ext)
        insert_all = pd.merge(left=insert_df, right=insert_ext, on='ID', suffixes=('', '_remove'), validate='one_to_one')
        insert_all.drop([i for i in insert_all.columns if 'remove' in i], axis=1, inplace=True)

        # Calculate the coordinate of insert entities
        insert_all['LowLeft'] = tuple(zip( insert_all['Text X'] - (insert_all['Text Width'] / 2), 
                                          insert_all['Text Y'] - (insert_all['Text Height'] / 2) ))

        insert_all['UpRight'] = tuple(zip( insert_all['Text X'] + (insert_all['Text Width'] / 2),
                                          insert_all['Text Y'] + (insert_all['Text Height'] / 2) ))

        # Drop the unnecessary columns from the dataframe
        insert_all.drop(['Text X','Text Y','Text Scale X','Text Scale Y','Text Width','Text Height'], axis=1, inplace=True)
        
        # Remove the incorrect piping text pattern
        pat_full = r'.*\d\"\-[A-Z]{1,4}\-[A-Z\d]{6,8}\-[A-Z].*' # 00"-XXXX-000000[00]-X
        insert_all = insert_all[insert_all.Name.str.contains(r'.*\d\"\-[A-Z]{1,4}\-[A-Z\d]{6,8}\-[A-Z].*', regex=True)]
        insert_all = insert_all.reset_index(drop=True)
        
        # Transform the coordinate of dxf file into ratio value
        insert_ratio = entities_dim_transform_ratio(frame_dim, insert_all)
        
        # Transform the coordinate ratio in the dxf file by scaling value        
        lowleft = [[x,y] for x,y in insert_ratio['LowLeft']]
        upright = [[x,y] for x,y in insert_ratio['UpRight']]

        for i in insert_ratio[insert_ratio['Rotation'] == 0].index:
            lowleft[i][0] = round(lowleft[i][0], 3) + 0.001
            lowleft[i][1] = round(lowleft[i][1], 3)
            upright[i][0] = round(upright[i][0], 3) - 0.001
            upright[i][1] = round(upright[i][1], 3) + 0.001

        for j in insert_ratio[insert_ratio['Rotation'] == 90].index:
            lowleft[j][0] = round(lowleft[j][0], 3)
            lowleft[j][1] = round(lowleft[j][1], 3) + 0.001
            upright[j][0] = round(upright[j][0], 3)
            upright[j][1] = round(upright[j][1], 3) - 0.001

        insert_ratio['LowLeft'] = tuple(lowleft)
        insert_ratio['UpRight'] = tuple(upright)        
        
    return insert_ratio

def text_bbox_wh(text_modelspace, text_df):
    
    ''' Calculate the width and height with adjustment of bounding box for insert entities '''
    
    if text_df.shape[0] == 0:
        text_ext = pd.DataFrame(columns=['ID','Name','Rotation','Text Width','Text Height','LowLeft X','LowLeft Y','Distance'])
    else:       
        text = text_modelspace

        text_idx = []
        text_name = []
        text_rot = []
        text_width = []
        text_height = []
        text_lowleft_x = []
        text_lowleft_y = []

        for t in text:
            if(t.dxf.text in text_df['Name'].to_list()):
                bbox = ezdxf.path.bbox(text2path.make_paths_from_entity(t))
                text_idx.append(t)
                text_name.append(t.dxf.text)
                text_rot.append((t.dxf.rotation))
                    
                if ((t.dxf.rotation > -10) | (t.dxf.rotation > 350)) & (t.dxf.rotation < 10): # Horizontal orientation
                    text_width.append( (bbox.size.x / 0.8) )
                    text_height.append( (bbox.size.y / 0.75) )
                    text_lowleft_x.append( (bbox.extmin[0] - 0.25) )
                    text_lowleft_y.append( (bbox.extmin[1] - 0.25) )

                elif (t.dxf.rotation > 80) & (t.dxf.rotation < 100): # Vertical orientation
                    text_width.append( (bbox.size.x / 0.75) + 0.05 )
                    text_height.append( (bbox.size.y / 0.75) - 1.5 )
                    text_lowleft_x.append( (bbox.extmin[0] - 0.5) )
                    text_lowleft_y.append( (bbox.extmin[1] - 0.25) )
                    
        text_rot = [round(rot, 0) for rot in text_rot]
                
        text_ext = pd.DataFrame(list(zip(text_idx, text_name, text_rot, text_width, text_height, text_lowleft_x,text_lowleft_y)),
                                columns=['ID','Name','Rotation','Text Width','Text Height','LowLeft X','LowLeft Y'])
        
        text_ext['Distance'] = ( (text_ext['LowLeft X'])**2 + (text_ext['LowLeft Y'])**2 )**0.5
                
        return text_ext
def text_bbox_xy(text_df, text_ext):
    
    ''' Calculate the coordinate both lower left (x0,y0) and upper right (x1,y1) of bounding box for insert entities'''
    
    # Merge and remove the duplicate columns
    if text_df.shape[0] == 0:
        text_all = pd.DataFrame(columns=['ID','Name','Rotation','Type','Pattern','LowLeft','UpRight'])
    else:
        text_all = pd.merge(left=text_df, right=text_ext, on='ID', suffixes=('', '_remove'), validate='one_to_one')
        text_all.drop([i for i in text_all.columns if 'remove' in i], axis=1, inplace=True)
        
        # Sort the text name based on rotation and distance
        if sum(text_all['Pattern'].str.startswith(('P','S'))) > 0:  
            text_all.sort_values('Rotation', ascending=True, inplace=True)
            text_all_h = text_all[text_all['Rotation'] == 0].sort_values('Distance', ascending=False)
            text_all_v = text_all[text_all['Rotation'] == 90].sort_values('Distance', ascending=True)
            text_all = pd.concat([text_all_h,text_all_v], axis=0, ignore_index=True, verify_integrity=True )

        # Calculate the coordinate of entities
        text_all['LowLeft'] = tuple(zip(text_all['LowLeft X'], text_all['LowLeft Y']))
        text_all['UpRight'] = tuple(zip(text_all['LowLeft X'] + text_all['Text Width'], text_all['LowLeft Y'] + text_all['Text Height']))
        
        # Drop the unnecessary columns from the dataframe
        text_all.drop(['Text Width','Text Height','LowLeft X','LowLeft Y','Distance'], axis=1, inplace=True)
    
    return text_all

def text_outofframe_cleansing(text_df_ratio, frame_threshold_ratio=0.84):
    
    ''' Clean some text mismatch location in the drawing out of the dataframe '''
    
    text_df_ratio = text_df_ratio.copy()
    
    text_df_ratio = text_df_ratio[text_df_ratio.LowLeft.map(lambda x: x[0]) <= frame_threshold_ratio].reset_index(drop=True)
    
    return text_df_ratio
  
def piping_text_full(modelspace):
    
    ''' Extract the information from text entities, which display in the full piping pattern in the model space from DXF file '''
    
    text = modelspace.query('TEXT')
    frame_dim = frame_dimension(modelspace)
    
    # Define pattern for filters of text entities
    pat_full = r'.*\d\"\-[A-Z]{1,4}\-[A-Z\d]{6,8}\-[A-Z].*' # 00"-XXXX-000000[00]-X
    
    # Create entities list for verification with criteria condition
    text_full_id = [t for t in text if bool(re.search(pat_full, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_full_id) == 0:
        text_full_ratio = pd.DataFrame(columns=['ID','Name','Rotation','Type','Pattern','LowLeft','UpRight'])
    else:
        # Full piping pattern dataframe
        text_full_name = [t.dxf.text for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_rot = [float(t.dxf.rotation) for t in text if bool(re.search(pat_full, t.dxf.text))]
        text_full_rot = [round(rot, 0) for rot in text_full_rot]
        text_full_dict = {'ID':text_full_id, 'Name':text_full_name, 'Rotation':text_full_rot}
        text_full_df = pd.DataFrame(text_full_dict).assign(Type = 'T', Pattern = 'F')
        
        # Clean the text rotation column
        text_full_df = text_rotation_cleansing(text_full_df)
        
        # Get the extension dataframe
        text_full_ext = text_bbox_wh(text, text_full_df)
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_full_all = text_bbox_xy(text_full_df, text_full_ext)
        
        # Transform the coordinate of dxf file into ratio value
        text_full_ratio = entities_dim_transform_ratio(frame_dim, text_full_all)
        
        # Remove the text that located out of the drawing frame area
        text_full_ratio = text_outofframe_cleansing(text_full_ratio)
        
        lowleft = [[x,y] for x,y in text_full_ratio['LowLeft']]
        upright = [[x,y] for x,y in text_full_ratio['UpRight']]

        for i in text_full_ratio[text_full_ratio['Rotation'] == 0].index:
            lowleft[i][0] = round(lowleft[i][0], 3) - 0.002
            lowleft[i][1] = round(lowleft[i][1], 3)
            upright[i][0] = round(upright[i][0], 3) - 0.005
            upright[i][1] = round(upright[i][1], 3)

        for j in text_full_ratio[text_full_ratio['Rotation'] == 90].index:
            lowleft[j][0] = round(lowleft[j][0], 3)
            lowleft[j][1] = round(lowleft[j][1], 3) - 0.001
            upright[j][0] = round(upright[j][0], 3)
            upright[j][1] = round(upright[j][1], 3) - 0.01

        text_full_ratio['LowLeft'] = tuple(lowleft)
        text_full_ratio['UpRight'] = tuple(upright)
    
    return text_full_ratio

def piping_text_pattern1(modelspace):
    
    ''' Extract the information from text entities, which display in the partial piping pattern (#1) in the model space from DXF file '''
    
    text = modelspace.query('TEXT')
    frame_dim = frame_dimension(modelspace)
    
    # Define pattern for filters of text entities
    pat_pref1 = r'\-[A-Z]{1,4}\-[0-9]{6,8}$' # -000000[00]
    pat_suff1 = r'^\-[A-Z][0-9]' # -X0
      
    # Create entities list for verification with criteria condition
    text_pref1_id = [t for t in text if bool(re.search(pat_pref1, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_pref1_id) == 0:
        text_pat1_ratio = pd.DataFrame(columns=['ID','Name','Rotation','Type','Pattern','LowLeft','UpRight'])
    else:
        # Partial piping pattern dataframe
        text_pref1_name = [t.dxf.text for t in text if bool(re.search(pat_pref1, t.dxf.text))]
        
        if len(text_pref1_name) > 0:
            text_pref1_rot = [t.dxf.rotation for t in text if bool(re.search(pat_pref1, t.dxf.text))]
            text_pref1_dict = {'ID':text_pref1_id, 'Name':text_pref1_name, 'Rotation':text_pref1_rot}
            text_pref1_df = pd.DataFrame(text_pref1_dict).assign(Type = 'T', Pattern = 'P1')

            text_suff1_id = [t for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_name = [t.dxf.text for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_rot = [t.dxf.rotation for t in text if bool(re.search(pat_suff1, t.dxf.text))]
            text_suff1_dict = {'ID':text_suff1_id, 'Name':text_suff1_name, 'Rotation':text_suff1_rot}
            text_suff1_df = pd.DataFrame(text_suff1_dict).assign(Type = 'T', Pattern = 'S1')

            text_pat1_df = pd.concat([text_pref1_df, text_suff1_df], axis=0, ignore_index=True, verify_integrity=True)
        
        # Clean the text rotation column
        text_pat1_df = text_rotation_cleansing(text_pat1_df)
        
        # Get the extension dataframe
        text_pat1_ext = text_bbox_wh(text, text_pat1_df)
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_pat1_all = text_bbox_xy(text_pat1_df, text_pat1_ext)
        
        # Transform the coordinate of dxf file into ratio value
        text_pat1_ratio = entities_dim_transform_ratio(frame_dim, text_pat1_all)
        
        lowleft = [[x,y] for x,y in text_pat1_ratio['LowLeft']]
        upright = [[x,y] for x,y in text_pat1_ratio['UpRight']]

        for i in text_pat1_ratio[text_pat1_ratio['Rotation'] == 0].index:
            lowleft[i][0] = round(lowleft[i][0], 3) - 0.001
            lowleft[i][1] = round(lowleft[i][1], 3)
            upright[i][0] = round(upright[i][0], 3) - 0.002
            upright[i][1] = round(upright[i][1], 3)

        for j in text_pat1_ratio[text_pat1_ratio['Rotation'] == 90].index:
            lowleft[j][0] = round(lowleft[j][0], 3)
            lowleft[j][1] = round(lowleft[j][1], 3) - 0.001
            upright[j][0] = round(upright[j][0], 3)
            upright[j][1] = round(upright[j][1], 3) - 0.002

        text_pat1_ratio['LowLeft'] = tuple(lowleft)
        text_pat1_ratio['UpRight'] = tuple(upright)
    
    return text_pat1_ratio

def piping_text_pattern2(modelspace):
    
    ''' Extract the information from text entities, which display in the partial piping pattern (#3) in the model space from DXF file '''
    
    text = modelspace.query('TEXT')
    frame_dim = frame_dimension(modelspace)
    
    # Define pattern for filters of text entities
    pat_pref2 = r'(\"\-[A-Z]{1,4}\-$)|(\"\-[A-Z]{1,4}$)' # 0"-XXXX-
    pat_suff2 = r'(^[0-9]{6,8}\-[A-Z][0-9])|(^\-[0-9]{6,8}\-[A-Z][0-9])' # 000000[00]-
      
    # Create entities list for verification with criteria condition
    text_pref2_id = [t for t in text if bool(re.search(pat_pref2, t.dxf.text))]
    
    # Create the text dataframe
    if len(text_pref2_id) == 0:
        text_pat2_ratio = pd.DataFrame(columns=['ID','Name','Rotation','Type','Pattern','LowLeft','UpRight'])
    else:
        # Partial piping pattern dataframe
        text_pref2_name = [t.dxf.text for t in text if bool(re.search(pat_pref2, t.dxf.text))]
        
        if len(text_pref2_name) > 0:
            text_pref2_rot = [t.dxf.rotation for t in text if bool(re.search(pat_pref2, t.dxf.text))]
            text_pref2_dict = {'ID':text_pref2_id, 'Name':text_pref2_name, 'Rotation':text_pref2_rot}
            text_pref2_df = pd.DataFrame(text_pref2_dict).assign(Type = 'T', Pattern = 'P2')

            text_suff2_id = [t for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_name = [t.dxf.text for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_rot = [t.dxf.rotation for t in text if bool(re.search(pat_suff2, t.dxf.text))]
            text_suff2_dict = {'ID':text_suff2_id, 'Name':text_suff2_name, 'Rotation':text_suff2_rot}
            text_suff2_df = pd.DataFrame(text_suff2_dict).assign(Type = 'T', Pattern = 'S2')

            text_pat2_df = pd.concat([text_pref2_df, text_suff2_df], axis=0, ignore_index=True, verify_integrity=True)
        
        # Clean the text rotation column
        text_pat2_df = text_rotation_cleansing(text_pat2_df)
        
        # Get the extension dataframe
        text_pat2_ext = text_bbox_wh(text, text_pat2_df)
        
        # Merge the lineList and lineExt by 'Text Name' columms
        text_pat2_all = text_bbox_xy(text_pat2_df, text_pat2_ext)
        
        # Transform the coordinate of dxf file into ratio value
        text_pat2_ratio = entities_dim_transform_ratio(frame_dim, text_pat2_all)

        lowleft = [[x,y] for x,y in text_pat2_ratio['LowLeft']]
        upright = [[x,y] for x,y in text_pat2_ratio['UpRight']]

        for i in text_pat2_ratio[text_pat2_ratio['Rotation'] == 0].index:
            lowleft[i][0] = round_up(lowleft[i][0], 3) - 0.002
            lowleft[i][1] = round_down(lowleft[i][1], 3)
            upright[i][0] = round_down(upright[i][0], 3) - 0.001
            upright[i][1] = round_up(upright[i][1], 3)

        for j in text_pat2_ratio[text_pat2_ratio['Rotation'] == 90].index:
            lowleft[j][0] = round_down(lowleft[j][0], 3)
            lowleft[j][1] = round_up(lowleft[j][1], 3) - 0.001
            upright[j][0] = round_up(upright[j][0], 3)
            upright[j][1] = round_down(upright[j][1], 3) - 0.002

            text_pat2_ratio['LowLeft'] = tuple(lowleft)
            text_pat2_ratio['UpRight'] = tuple(upright)
    
    return text_pat2_ratio

def info_extract_pid_uhv(name: Path):
    
    ''' Extract the information from the DWG file, and then save the relevant information into *.csv file '''
    
    # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
    os.chdir(name)
        
    dxf_folder = ".\\DXF"
    raster_folder = ".\\PNG"
    list_dxf_files = get_file_list(dxf_folder)
    list_raster_files = get_file_list(raster_folder)
    
    if len(list_dxf_files) != len(list_raster_files):
        sys.exit('Numbers of drawing files (.dxf) do not equal to raster (.png, .jpg) files.')
    
    list_data_files = list(zip(list_dxf_files,list_raster_files))
    list_data_files = pd.DataFrame(list_data_files, columns=['DXF','PNG'])
         
    for idx in tqdm(list_data_files.index):
        
        # Get the file location
        dxf_filename = list_data_files.loc[idx,'DXF']
        raster_filename = list_data_files.loc[idx,'PNG']
        
        # Create and query the model space
        model_space = get_modelspace(dxf_filename)
        
        # Get the drawing dimension from model space
        frame_dim = frame_dimension(model_space)
        
        # Create the component dataframes of each piping text pattern
        insert_ratio_df = piping_insert_full(model_space)
        text_full_ratio_df = piping_text_full(model_space)
        text_pat1_ratio_df = piping_text_pattern1(model_space)
        text_pat2_ratio_df = piping_text_pattern2(model_space)
        
        # Transform the scale coordinate ratio from dxf file into coordinate for raster file
        insert_df = entities_dim_transform_raster(raster_filename, insert_ratio_df)
        text_full_df = entities_dim_transform_raster(raster_filename, text_full_ratio_df)
        text_pat1_df = entities_dim_transform_raster(raster_filename, text_pat1_ratio_df)
        text_pat2_df = entities_dim_transform_raster(raster_filename, text_pat2_ratio_df)
        
        # Append all of component dataframes
        piping_df = pd.concat([insert_df,text_full_df,text_pat1_df,text_pat2_df], axis=0,
                              ignore_index=True, verify_integrity=True)
        
        # Add the filename
        listname = re.split(r'\\|\.', dxf_filename)
        filename = listname[-2]
        piping_df = piping_df.assign(Filename = filename)      
                
        # Define related parameters and check the existing save folder
        list_folders = os.listdir('.\\DXF')
        save_csv_folder = '.\\CSV'
        trim_char = ['','DXF',filename,'dxf']
    
        if not os.path.exists(save_csv_folder):
            os.makedirs(save_csv_folder)
        
        # Save file CSV
        if bool(len(list_dxf_files) != 0):
            prior_folder = [folder for folder in listname if folder not in trim_char]
            prior_folder = "".join(prior_folder)
            
            # Check the whether if existing folder is created        
            if not os.path.exists(save_csv_folder+'\\'+prior_folder): 
                os.makedirs(save_csv_folder+'\\'+prior_folder)
            saveinfo_path = save_csv_folder+'\\'+prior_folder+'\\'+filename+'.csv'
        else:
            saveinfo_path = save_csv_folder+'\\'+file_name+'.csv'
        
        piping_df.to_csv(saveinfo_path)
        print('Saving location of file:', saveinfo_path)
        
    print('Information extraction is now complete!!!')
    gc.collect()
    
# set your working directory:
DIR = Path(".\\Use Case Project").expanduser()

# Testing!!!
# Ensure the working directory before executing!!!
# All drawing file must be located in the 'DWG' sub-folder

info_extract_pid_uhv(DIR)
