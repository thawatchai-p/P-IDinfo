from pathlib import Path
import subprocess
import os

folder_path = Path(".\\Use Case Project").expanduser() 

def dwg_to_dxf(name: Path):
  
  ''' Convert the DWG file into DXF file format '''
  
  # Set working directory, which there is sub-folder name 'DWG' consists of *.dwg files
  os.chdir(name)
  
  # Check whether if the output folder is create
  output_folder = 'DXF'
  if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    
  # Please install Teigha File Converter by copy and paste the as following link in URL:
  # https://teigha-file-converter.software.informer.com/

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
  INPUT_FOLDER = "./DWG"
  OUTPUT_FOLDER = output_folder
  OUTVER = "ACAD2018"
  OUTFORMAT = "DXF"
  RECURSIVE = "1"
  AUDIT = "1"
  INPUTFILTER = "*.DWG"

  # Command to run
  cmd = [TEIGHA_PATH, INPUT_FOLDER, OUTPUT_FOLDER, OUTVER, OUTFORMAT, RECURSIVE, AUDIT, INPUTFILTER]

  # Run
  subprocess.run(cmd, shell=True)
