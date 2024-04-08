import aspose.threed as a3d
import argparse
import os
import bpy
import json
import shutil
import textures as Textures # custom module created to store texture info

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

class TscnGen:    
    def __init__(self, input_folder, output_folder, scale):
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
        # don't generate textures more than once
        if texture not in self.texture_index:
            # handle PBR textures (require .jpgs)
            if texture in Textures.texture_dict:
                t_info = Textures.texture_dict[texture]
                self.sub_resource += f'[sub_resource type="SpatialMaterial" id={self.sub_resource_id}]\n'

                for jpg, value in t_info.jpg_dict.items():
                    if jpg in ["albedo", "roughness", "metallic"]:
                        self.sub_resource += f"{jpg}_texture = ExtResource( {self.ext_resource_id} )\n"
                    elif jpg == "normal":
                        self.sub_resource += Textures.NORMAL_OPTIONS + f"normal_texture = ExtResource( {self.ext_resource_id} )\n"
                    elif jpg == "depth":
                        self.sub_resource += Textures.DEPTH_OPTIONS + f"depth_texture = ExtResource( {self.ext_resource_id} )\n"
                    # add .jpg as ext_resource
                    self.ext_resource += f'[ext_resource path="res://{Textures.TEXTURE_FOLDER}/{t_info.folder}/{value}" type="Texture" id={self.ext_resource_id}]\n'
                    self.ext_resource_id += 1

                # add uv1_scale if texture has it
                if t_info.uv1_scale:
                    self.sub_resource += f"uv1_scale = {t_info.uv1_scale}\n"

            # handle textures which don't need .jpgs (only need sub_resource)
            elif texture in Textures.other_textures:
                self.sub_resource += f'[sub_resource type="SpatialMaterial" id={self.sub_resource_id}]\n{Textures.other_textures[texture]}'

            self.sub_resource += "\n"
                
            # add the sub resource's index to texture_index so we can use it later 
            self.texture_index[texture] = self.sub_resource_id
            self.sub_resource_id += 1 

    def add_obj_file(self, stl_file_extless, uv_map, mesh_compression, texture):
        # reset bpy
        bpy.ops.wm.read_factory_settings(use_empty=True)
        # import .stl into bpy
        bpy.ops.import_mesh.stl(filepath = f"{self.input_folder}/{stl_file_extless}.stl")
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
            except KeyError as e:
                print(f"no uv map generated for {stl_file_extless} due to invalid uv_map")

            # Toggle out of Edit Mode
            bpy.ops.object.mode_set(mode='OBJECT')
            # Deselect the object
            obj.select_set(False)

        # Export to obj
        bpy.ops.wm.obj_export(filepath = f"{self.output_folder}/{stl_file_extless}.obj")
        # remove the .mtl file
        os.remove(f"{self.output_folder}/{stl_file_extless}.mtl")

        # add to tscn file
        self.nodes += f'[node name="{stl_file_extless}" type="MeshInstance" parent="."]\nmesh = ExtResource( {self.ext_resource_id} )' \
                    + f'\nmaterial/0 = SubResource( {self.texture_index[texture]} )\n\n'
        self.ext_resource += f'[ext_resource path="res://models/{self.output_folder}/{stl_file_extless}.obj" type="ArrayMesh" id={self.ext_resource_id}]\n'
        self.ext_resource_id += 1

    def add_collisions(self, stl_file_extless):
        # generate fbx file from stl file to create collisions
        fbx_file = f"{self.output_folder}/{stl_file_extless}.fbx"
        scene = a3d.Scene.from_file(f"{self.input_folder}/{stl_file_extless}.stl")
        scene.save(fbx_file)

        # reset bpy
        bpy.ops.wm.read_factory_settings(use_empty=True)
        # import .fbx into bpy
        bpy.ops.import_scene.fbx(filepath = fbx_file)

        # rename all objects as -colonly
        for obj_index in range(len(bpy.data.objects)):
            # every re-name moves the object to the back of the list. 
            bpy.data.objects[0].name = "Volume" + str(obj_index) + "-colonly"

        # export to .gltf
        bpy.ops.export_scene.gltf(filepath = f"{self.output_folder}/{stl_file_extless}.gltf")

        # remove the fbx file
        os.remove(fbx_file)

        # add to tscn file  
        self.nodes += f'[node name="{stl_file_extless}Col" parent="." instance=ExtResource( {self.ext_resource_id} )]\n\n'
        self.ext_resource += f'[ext_resource path="res://models/{self.output_folder}/{stl_file_extless}.glb" type="PackedScene" id={self.ext_resource_id}]\n'
        self.ext_resource_id += 1

    def write_tscn_file(self):
        with open(f"{self.output_folder}/{self.output_folder}.tscn", 'w') as tscn_file:
            tscn_file.write(f"[gd_scene load_steps={self.ext_resource_id + self.sub_resource_id} format=2]\n\n{self.ext_resource}\n{self.sub_resource}{self.nodes}")


def make_folder(folder):
    try:
        os.mkdir(f"./{folder}")
    # delete the folder and remake it if it does exist
    except OSError as error:
        print(f"NOTICE: {folder} folder already exists, so it was deleted and remade")
        shutil.rmtree(folder) # delete folder and contents
        os.mkdir(f"./{folder}")


def main():
    # argparse to take in input.txt
    parser = argparse.ArgumentParser(prog = ".stl to .obj and .tscn file converter")
    parser.add_argument("input_file", type = str, help = "input json filename")
    args = parser.parse_args()

    # load input json dictionary
    with open(args.input_file, 'r') as f:
        data = json.load(f)

    header = data["header"]
    input_folder = header["input_folder"]
    output_folder = header["output_folder"]

    # load textures
    Textures.load_textures("textures.json")
    if "extra_textures" in header: 
        Textures.load_textures(header["extra_textures"])
        
    # make the output folder
    make_folder(output_folder)

    # initialize tscn class object (with optional scale)
    scale = 1
    if "scale" in header:
        scale = header["scale"]
    tscn = TscnGen(input_folder, output_folder, scale)

    ##################################
    # iterate through all .stl files #
    ##################################
    for m in data["meshes"]:
        stl_file_extless, _ = os.path.splitext(m["stl_file"])
        # generation
        tscn.add_texture(m["texture"])
        tscn.add_obj_file(stl_file_extless, m["uv_map"], m["mesh_compression"], m["texture"])
        if m["collisions"]:
            tscn.add_collisions(stl_file_extless)

    tscn.write_tscn_file()    


if __name__ == "__main__":
    main()