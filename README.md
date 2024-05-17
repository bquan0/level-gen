# level-gen

### How to use cubitExportSTL.py
This module will export all groups in cubit into .stl files AND create a .json file, which can be used as input for stl_to_tscn.py
1. Open Cubit and import the cubitExportSTL module
```
import sys
sys.path.append(“<folder that contains cubitExportSTL.py>”)
import cubitExportSTL
```
2. Create groups of Volumes. Each group will be exported to its own .stl file.
3. Run this in Cubit:
`cubitExportSTL.export_groups(cubit, "<folder to export stl files and .json file to>")`