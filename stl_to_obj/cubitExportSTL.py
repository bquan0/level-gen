from pathlib import Path
import argparse
import json
import csv

import cubit

def export_groups_CL(output_folder, sat_file, template='.csv'):
    """ Used in terminal to export .stl files based on the groups of an ACIS file.
    Also generates a .json file which is a template input to the stl_to_tscn module.

    Parameters
    ----------
    output_folder : str
        where output .stl and .json files should be placed
    sat_file : str
        the ACIS file
    template : str
        the file format of the template file (either .json or .csv)
    """
    cubit.cmd(f'import acis "{sat_file}" nofreesurfaces heal attributes_on separate_bodies')
    export_groups(output_folder, template)

def export_groups(output_folder, template='.csv'):
    """ Used in Cubit's Python command line to export .stl files based on the groups of an ACIS file.
    Also generates a .json file which is a template input to the stl_to_tscn module.

    Parameters
    ----------
    output_folder : str
        where output .stl and .json files should be placed
    template : str
        the file format of the template file (either .json or .csv)
    """
    # json file dictionaries
    header_dict = {
        "input_folder": "",
        "output_folder": "",
        "scale": 0.01,
        "extra_textures": "more_textures.json" 
    }
    meshes = []

    # get tuples of (group_name, id)
    groups = cubit.group_names_ids()

    for group in groups:
        group_name = group[0]
        if group_name == "picked":
            continue
        stl_filepath = Path(output_folder) / Path(group_name).with_suffix('.stl')
        volumes = cubit.get_group_volumes(group[1])
        cubit.cmd(f'export stl "{stl_filepath}" volume {str(volumes)[1:-1]} overwrite')

        # add .stl mesh entry to .json file
        mesh_dict = {
            "stl_file": f"{group_name}.stl",
            "uv_map": "cube",
            "texture": group_name, 
            "collisions": True,
            "mesh_compression": "limited_dissolve"
        }
        meshes.append(mesh_dict)

    json_dict = {
        "header": header_dict,
        "meshes": meshes
    }

    if template == '.json':
        with open(Path(output_folder) / Path("input").with_suffix('.json'), 'w') as json_file:
            json_string = json.dumps(json_dict, indent = 4)
            json_file.write(json_string)
    # default is .csv file
    else:
        with open(Path(output_folder) / Path("input").with_suffix('.csv'), 'w', newline='',) as csv_file:
            # write the header dict
            fieldnames = ["input_folder", "output_folder", "scale", "extra_textures"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(header_dict)

            # write the meshes array
            fieldnames = ["stl_file", "uv_map", "texture", "collisions", "mesh_compression"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for mesh in meshes:
                writer.writerow(mesh)

def main():
    parser = argparse.ArgumentParser(prog = "export groups in ACIS file to .stl files")
    parser.add_argument("output_folder", type = str, help = "location to store .stl and template files")
    parser.add_argument("sat_file", type = str, help = "location of ACIS file")
    parser.add_argument("--template", "-t", type = str, default=".csv", help = "type of output template file (.json or .csv)")
    args = parser.parse_args()

    export_groups_CL(args.output_folder, args.sat_file, args.template)

if __name__ == "__main__":
    main()