from pathlib import Path
import json

def export_groups(cubit, output_folder):
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
        stl_filepath = Path(output_folder) / Path(group_name).with_suffix('.stl')
        volumes = cubit.get_group_volumes(group[1])
        cubit.cmd(f'export stl "{stl_filepath}" volume {str(volumes)[1:-1]} overwrite')

        # add .stl mesh entry to .json file
        mesh_dict = {
            "stl_file": f"{group_name}.stl",
            "uv_map": "cube",
            "texture": "Plaster", 
            "collisions": True,
            "mesh_compression": "limited_dissolve"
        }
        meshes.append(mesh_dict)

    json_dict = {
        "header": header_dict,
        "meshes": meshes
    }

    with open(Path(output_folder) / Path("input").with_suffix('.json'), 'w') as json_file:
        json_string = json.dumps(json_dict, indent = 4)
        json_file.write(json_string)