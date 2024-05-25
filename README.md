# level-gen

## How to use cubitExportSTL.py
This module will export all groups in cubit into .stl files AND create a template file, which can be used as input for stl_to_tscn.py
### To export groups for an ACIS (.sat) file that already has groups
`python3 cubitExportSTL.py [output_folder] [sat_file location] [template type]` 
This allows you to do everything from the command line. (You don't have to open Cubit.)

### To export groups while using Cubit GUI
1. Open Cubit and import the cubitExportSTL module
`import cubitExportSTL`
If you get a `ModuleNotFoundError`, you can either run this:
```
import sys
sys.path.append(“<folder that contains cubitExportSTL.py>”)
```
or search up a way to add the folder that contains the module to your PATH env variable. 
2. Create groups of Volumes. Each group will be exported to its own .stl file.
3. Run this in Cubit:
`cubitExportSTL.export_groups(cubit, "<folder to export stl files and .json file to>")`