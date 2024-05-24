from pathlib import Path
from io import StringIO
import argparse
import json
import csv
import shutil
import warnings

import aspose.threed as a3d
import bpy

import textures # custom module created to store texture info

# example run
# python3.10 stl_to_tscn.py input.json

# uv map functions from bpy
UV_MAPS = {
    "smart": bpy.ops.uv.smart_project,
    "cube": bpy.ops.uv.cube_project,
    "cylinder": bpy.ops.uv.cylinder_project,
    "sphere": bpy.ops.uv.sphere_project,
    "unwrap": bpy.ops.uv.unwrap
}

class TscnGenerator:    
    """ Class to generate the ext_resource, sub_resource, and node sections of scene files
    
    Attributes
    ----------
    input_folder : str
        location of the .stl files
    output_folder : str
        where output .obj, .glb, and .tscn files should be placed
    ext_resource : str
        stores the references to .jpg, .obj, .glb files that the scene uses
    ext_resource_id : int
        index of the next ext_resource to be added
    sub_resource : str
        constructions of SpatialMaterials (textures)
    sub_resource_id : int
        index of the next sub_resource to be added
    nodes : str
        MeshInstances and collisions scenes
    texture_index : dict
        stores the sub_resource_id of generated textures

    Methods
    -------
    add_texture(texture):
        Adds a texture to sub_resource and stores its index in texture_index
    add_obj_file(stl_file_extless, uv_map, mesh_compression, texture):
        Generates an .obj from an .stl and applies a texture to the .obj 
    add_collisions(stl_file_extless):
        Generates a .glb collision scene file from an .stl
    write_tscn_file():
        Creates the .tscn file and writes ext_resource, sub_resource, and node to it.
    """
    def __init__(self, input_folder, output_folder, scale):
        """
        Parameters
        ----------
        input_folder : str
            location of the .stl files
        output_folder : str
            where output .obj, .glb, and .tscn files should be placed
        scale : float
            the scale of the models (ex: if the model was in centimeters, scale = 0.01)
        """
        self.input_folder = input_folder
        self.output_folder = output_folder

        # all the .obj, .glb, .jpg (textures)
        self.ext_resource = ""
        self.ext_resource_id = 1

        # SpatialMaterials (construction of textures)
        self.sub_resource = ""
        self.sub_resource_id = 1

        # MeshInstances and collision scenes (.glb)
        self.nodes = f'[node name="{output_folder}" type="Spatial"]\n'
        if scale != 1:
            self.nodes += f'transform = Transform( {scale}, 0, 0, 0, {scale}, 0, 0, 0, {scale}, 0, 0, 0 )\n'
        self.nodes += "\n" # add extra new line to prepare for next node

        # keep track of textures so we don't generate them more than once
        self.texture_index = dict()

    def add_texture(self, texture):
        """
        Adds a texture to sub_resource and stores its index in texture_index.
        
        Parameters
        ----------
        texture : str
            name of a texture that can be found in the dictionary of the textures module. 
        """
        # don't generate textures more than once
        if texture not in self.texture_index:
            # handle PBR textures (require .jpgs)
            if texture in textures.texture_dict:
                t_info = textures.texture_dict[texture]
                self.sub_resource += f'[sub_resource type="SpatialMaterial" id={self.sub_resource_id}]\n'

                for jpg, value in t_info.jpg_dict.items():
                    if jpg in ["albedo", "roughness", "metallic"]:
                        self.sub_resource += f"{jpg}_texture = ExtResource( {self.ext_resource_id} )\n"
                    elif jpg == "normal":
                        self.sub_resource += textures.NORMAL_OPTIONS + f"normal_texture = ExtResource( {self.ext_resource_id} )\n"
                    elif jpg == "depth":
                        self.sub_resource += textures.DEPTH_OPTIONS + f"depth_texture = ExtResource( {self.ext_resource_id} )\n"
                    # add .jpg as ext_resource
                    self.ext_resource += f'[ext_resource path="res://{textures.TEXTURE_FOLDER}/{t_info.folder}/{value}" type="Texture" id={self.ext_resource_id}]\n'
                    self.ext_resource_id += 1

                # add uv1_scale if texture has it
                if t_info.uv1_scale:
                    self.sub_resource += f"uv1_scale = {t_info.uv1_scale}\n"

            # handle textures which don't need .jpgs (only need sub_resource)
            elif texture in textures.other_textures:
                self.sub_resource += f'[sub_resource type="SpatialMaterial" id={self.sub_resource_id}]\n{textures.other_textures[texture]}'

            self.sub_resource += "\n"
                
            # add the sub resource's index to texture_index so we can use it later 
            self.texture_index[texture] = self.sub_resource_id
            self.sub_resource_id += 1 

    def add_obj_file(self, stl_file_extless, uv_map, mesh_compression, texture):
        """
        Generates an .obj from an .stl and applies a texture to the .obj 

        Parameters
        ----------
        stl_file_extless : str
            name of the .stl file without the extension
        uv_map : str
            type of texture mapping to apply to the mesh
        mesh_compression : str
            how to combine the triangles of the .stl file
        texture : str
            texture to apply to this .stl file 
        """
        # reset bpy
        bpy.ops.wm.read_factory_settings(use_empty=True)
        # import .stl into bpy
        import_path = Path(self.input_folder) / Path(stl_file_extless).with_suffix('.stl')
        bpy.ops.import_mesh.stl(filepath=str(import_path))
        # Get all objects in selection
        selection = bpy.context.selected_objects
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        for obj in selection:
            # Select each object
            obj.select_set(True)
            # Make it active
            bpy.context.view_layer.objects.active = obj
            # Toggle into Edit Mode
            bpy.ops.object.mode_set(mode='EDIT')
            # Select the geometry
            bpy.ops.mesh.select_all(action='SELECT')

            # Remove unnecessary faces 
            if mesh_compression == "limited_dissolve": 
                bpy.ops.mesh.dissolve_limited()
            elif mesh_compression == "tris_to_quads":
                bpy.ops.mesh.tris_convert_to_quads() 

            # Call project operator to generate uv maps
            try:
                UV_MAPS[uv_map]()
            except KeyError:
                e = KeyError(f"no uv map generated for {stl_file_extless} due to invalid uv_map")
                raise e

            # Toggle out of Edit Mode
            bpy.ops.object.mode_set(mode='OBJECT')
            # Deselect the object
            obj.select_set(False)

        # Export to obj
        export_path = Path(self.output_folder) / Path(stl_file_extless).with_suffix('.obj')
        bpy.ops.wm.obj_export(filepath = str(export_path))
        
        # remove the .mtl file
        mtl_filepath = Path(self.output_folder) / Path(stl_file_extless).with_suffix('.mtl')
        Path.unlink(mtl_filepath)

        # add to tscn file
        self.nodes += f'[node name="{stl_file_extless}" type="MeshInstance" parent="."]\nmesh = ExtResource( {self.ext_resource_id} )' \
                    + f'\nmaterial/0 = SubResource( {self.texture_index[texture]} )\n\n'
        self.ext_resource += f'[ext_resource path="res://models/{self.output_folder}/{stl_file_extless}.obj" type="ArrayMesh" id={self.ext_resource_id}]\n'
        self.ext_resource_id += 1

    def add_collisions(self, stl_file_extless):
        """
        Generates a .glb collision scene file from an .stl

        Parameters
        ----------
        stl_file_extless : str
            name of the .stl file without the extension
        """
        # generate fbx file from stl file to create collisions
        stl_file = Path(self.input_folder) / Path(stl_file_extless).with_suffix('.stl')
        fbx_file = Path(self.output_folder) / Path(stl_file_extless).with_suffix('.fbx')
        scene = a3d.Scene.from_file(str(stl_file))
        scene.save(str(fbx_file))

        # reset bpy
        bpy.ops.wm.read_factory_settings(use_empty=True)
        # import .fbx into bpy
        bpy.ops.import_scene.fbx(filepath = str(fbx_file))

        # rename all objects as -colonly
        for obj_index, obj in enumerate(bpy.data.objects):
            # every re-name moves the object to the back of the list. 
            obj.name = "Volume" + str(obj_index) + "-colonly"

        # export to .gltf
        bpy.ops.export_scene.gltf(filepath = f"{self.output_folder}/{stl_file_extless}.gltf")

        # remove the fbx file
        Path.unlink(fbx_file)

        # add to tscn file  
        self.nodes += f'[node name="{stl_file_extless}Col" parent="." instance=ExtResource( {self.ext_resource_id} )]\n\n'
        self.ext_resource += f'[ext_resource path="res://models/{self.output_folder}/{stl_file_extless}.glb" type="PackedScene" id={self.ext_resource_id}]\n'
        self.ext_resource_id += 1

    def write_tscn_file(self):
        """ Creates the .tscn file and writes ext_resource, sub_resource, and node to it. """
        with open(f"{self.output_folder}/{self.output_folder}.tscn", 'w') as tscn_file:
            tscn_file.write(f"[gd_scene load_steps={self.ext_resource_id + self.sub_resource_id} format=2]\n\n{self.ext_resource}\n{self.sub_resource}{self.nodes}")


def make_folder(folder):
    try:
        p = Path.cwd() / Path(folder)
        p.mkdir()
    # delete the folder and remake it if it does exist
    except FileExistsError:
        warnings.warn(f"{folder} folder already exists, so it was deleted and remade", UserWarning)
        shutil.rmtree(p) # delete folder and contents
        p.mkdir()

def csvToDict(csv_filepath):
    with open(csv_filepath) as csv_file:
        # split csv_file into two strings
        # header is the first 2 lines, meshes is the rest.
        csv_list = list(csv_file)
        header_string = f'{csv_list[0]}\n{csv_list[1]}'
        csv_list.pop(0)
        csv_list.pop(0)
        meshes_string = '\n'.join(csv_list)

        # create header dict
        reader = csv.DictReader(StringIO(header_string))
        for row in reader:
            row["scale"] = float(row["scale"])
            header = row # there should only be one row in reader, that's why this works

        # create meshes array
        meshes = []
        reader = csv.DictReader(StringIO(meshes_string))
        for row in reader:
            if row["collisions"].casefold() == "true".casefold():
                row["collisions"] = True
            else:
                row["collisions"] = False
            meshes.append(row)
        
    return {"header": header, "meshes": meshes}

def main():
    parser = argparse.ArgumentParser(prog = ".stl to .obj and .tscn file converter")
    parser.add_argument("input_file", type = str, help = "input filename (.json or .csv)")
    args = parser.parse_args()

    # load data dictionary differently based on whether it is .json or .csv
    inputSuffix = Path(args.input_file).suffix
    if inputSuffix == ".json":
        with open(args.input_file, 'r') as f:
            data = json.load(f)
    elif inputSuffix == ".csv":
        data = csvToDict(args.input_file)
    else:
        raise Exception("input file was not a .json or .csv file")

    header = data["header"]
    input_folder = header["input_folder"]
    output_folder = header["output_folder"]

    # load textures
    textures.load_textures("textures.json")
    if "extra_textures" in header: 
        textures.load_textures(header["extra_textures"])
        
    # make the output folder
    make_folder(output_folder)

    # initialize tscn class object (with optional scale)
    scale = 1
    if "scale" in header:
        scale = header["scale"]
    tscn = TscnGenerator(input_folder, output_folder, scale)

    ##################################
    # iterate through all .stl files #
    ##################################
    for m in data["meshes"]:
        stl_file_extless = Path(m["stl_file"]).stem
        # generation
        tscn.add_texture(m["texture"])
        tscn.add_obj_file(stl_file_extless, m["uv_map"], m["mesh_compression"], m["texture"])
        if m["collisions"]:
            tscn.add_collisions(stl_file_extless)

    tscn.write_tscn_file()    


if __name__ == "__main__":
    main()