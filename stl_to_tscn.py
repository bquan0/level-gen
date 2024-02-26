import aspose.threed as a3d
import argparse
import os
import bpy
import json
import textures as Textures # custom module created to store texture info

# example run
# python3.10 stl_to_tscn.py input.txt

# generates an .obj file with uv maps from an .stl file
def generate_obj_file(stl_file, output_prefix, uv_map_type):
    # reset bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # import .stl into bpy
    bpy.ops.import_mesh.stl(filepath = stl_file)

    # Get all objects in selection
    selection = bpy.context.selected_objects

    # Get the active object
    active_object = bpy.context.active_object

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

        # Use limited dissolve to remove unnecessary faces 
        bpy.ops.mesh.dissolve_limited()
        # Call project operator to generate uv maps
        if uv_map_type == "smart":
            bpy.ops.uv.smart_project()
        elif uv_map_type == "cube":
            bpy.ops.uv.cube_project()
        elif uv_map_type == "cylinder":
            bpy.ops.uv.cylinder_project()
        elif uv_map_type == "sphere":
            bpy.ops.uv.sphere_project()
        elif uv_map_type == "unwrap":
            bpy.ops.uv.unwrap()

        # Toggle out of Edit Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Deselect the object
        obj.select_set(False)

    # Restore the selection
    for obj in selection:
        obj.select_set(True)

    # Restore the active object
    bpy.context.view_layer.objects.active = active_object

    # Export to obj
    bpy.ops.wm.obj_export(filepath = output_prefix + ".obj")

    # remove the .mtl file
    os.remove(output_prefix + ".mtl")



def generate_collisons(stl_file, output_prefix):
    # generate fbx file from stl file to create collisions
    fbx_file = output_prefix + ".fbx"
    scene = a3d.Scene.from_file(stl_file)
    scene.save(fbx_file)

    # reset bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # import .fbx into bpy
    bpy.ops.import_scene.fbx(filepath = fbx_file)

    # rename all objects as -colonly
    num_objs = len(bpy.data.objects)
    for k in range(num_objs):
        # every re-name moves the object to the back of the list. 
        bpy.data.objects[0].name = "Volume" + str(k) + "-colonly"

    # export to .gltf
    bpy.ops.export_scene.gltf(filepath = output_prefix + ".gltf")

    # remove the fbx file
    os.remove(fbx_file)


    
#################
# Program Start #
#################

# argparse to take in input.txt
parser = argparse.ArgumentParser(prog = ".stl to .obj and .tscn file converter")
parser.add_argument("input_file", type = str, help = "input json filename")
args = parser.parse_args()

# read in input .json file
with open(args.input_file, 'r') as f:
    ######################
    # .tscn file strings #
    ######################
    # all the .obj, .glb, .jpg (textures)
    ext_resource = ""
    ext_resource_id = 1

    # SpatialMaterials (construction of textures)
    sub_resource = ""
    sub_resource_id = 1

    # MeshInstances and collision scenes (.glb)
    nodes = ""


    ###################
    # parse json file #
    ###################
    # load JSON object as dictionary
    data = json.load(f)

    header = data["header"]

    # make the output folder if it doesn't already exist
    output_folder = header["output_folder"]
    try:
        os.mkdir("./" + output_folder)
    except OSError as error:
        print("NOTICE: " + output_folder + " folder already exists")

    # (optional) load extra textures 
    if "extra_textures" in header: 
        Textures.add_textures(header["extra_textures"])
    
    # initialize root node
    nodes += "[node name=\"" + output_folder + "\" type=\"Spatial\"]\n"

    # (optional) set scale of scene
    if "scale" in header:
        scale = header["scale"]
        nodes += "transform = Transform( " + str(scale) + ", 0, 0, 0, " + str(scale) + ", 0, 0, 0, " + str(scale) + ", 0, 0, 0 )\n"
    nodes += "\n" # add extra new line to prepare for next node


    ##################################
    # iterate through all .stl files #
    ##################################
    meshes = data["meshes"]

    # keep track of textures so we don't generate them more than once
    texture_index = dict()

    for m in meshes:
        ####################
        # generate texture #
        ####################
        texture = m["texture"]

        # don't generate textures more than once
        if texture not in texture_index:
            # check if it's a PBR texture (require .jpgs)
            if texture in Textures.texture_dict:
                sub_resource += "[sub_resource type=\"SpatialMaterial\" id=" + str(sub_resource_id) + "]\n"
                for jpg in Textures.texture_dict[texture].jpg_dict:
                    value = Textures.texture_dict[texture].jpg_dict[jpg]
                    # form the ext_resource
                    ext_resource += "[ext_resource path=\"res://" + Textures.texture_folder + "/" + Textures.texture_dict[texture].folder \
                                    + "/" + value + "\" type=\"Texture\" id=" + str(ext_resource_id) + "]\n"
                    # add to sub_resource
                    if jpg == "albedo":
                        sub_resource += "albedo_texture = ExtResource( " + str(ext_resource_id) + " )\n"
                    elif jpg == "roughness":
                        sub_resource += "roughness_texture = ExtResource( " + str(ext_resource_id) + " )\n"
                    elif jpg == "normal":
                        sub_resource += Textures.normal_options + "normal_texture = ExtResource( " + str(ext_resource_id) + " )\n"
                    elif jpg == "depth":
                        sub_resource += Textures.depth_options + "depth_texture = ExtResource( " + str(ext_resource_id) + " )\n"

                    # don't forget to increment ext_resource_id for the next one
                    ext_resource_id += 1

                # add uv1_scale if texture has it
                if Textures.texture_dict[texture].uv1_scale:
                    sub_resource += "uv1_scale = " + Textures.texture_dict[texture].uv1_scale + "\n"

                # add the sub resource's index to texture_index so we can use it later 
                sub_resource += "\n"
                texture_index[texture] = sub_resource_id
                sub_resource_id += 1 

            elif texture in Textures.other_textures:
                # only need sub_resource
                sub_resource += "[sub_resource type=\"SpatialMaterial\" id=" + str(sub_resource_id) + "]\n" + Textures.other_textures[texture]
                
                # add the sub resource's index to texture_index so we can use it later 
                sub_resource += "\n"
                texture_index[texture] = sub_resource_id
                sub_resource_id += 1 


        #####################
        # generate obj mesh #
        #####################
        stl_file = m["stl_file"]

        # output filename without a file extension
        output_prefix = output_folder + "/" + stl_file[:-4]
        
        # Generate .obj file
        generate_obj_file(stl_file, output_prefix, m["uv_map"])
        # add it to ext_resource
        ext_resource += "[ext_resource path=\"res://models/" + output_prefix + \
                        ".obj\" type=\"ArrayMesh\" id=" + str(ext_resource_id) + "]\n"
        # add it to nodes
        nodes += "[node name=\"" + stl_file[:-4] + "\" type=\"MeshInstance\" parent=\".\"]\nmesh = ExtResource( " \
                    + str(ext_resource_id) + " )\nmaterial/0 = SubResource( " + str(texture_index[texture]) + " )\n\n"

        # move on to next ext_resource
        ext_resource_id = ext_resource_id + 1

        #######################
        # Generate collisions #
        #######################
        if m["collisions"]:
            generate_collisons(stl_file, output_prefix)
            # add it to ext_resource
            ext_resource += "[ext_resource path=\"res://models/" + output_prefix + \
                            ".glb\" type=\"PackedScene\" id=" + str(ext_resource_id) + "]\n"
                        
            nodes += "[node name=\"" + stl_file[:-4] + "Col\" parent=\".\" instance=ExtResource( " + str(ext_resource_id) + " )]\n\n"

            # move on to next ext_resource
            ext_resource_id = ext_resource_id + 1

    with open(output_folder + "/" + output_folder + ".tscn", 'w') as tscn_file:
        tscn_file.write("[gd_scene load_steps=" + str(ext_resource_id + sub_resource_id) + " format=2]\n\n"
            + ext_resource + "\n" + sub_resource + nodes)
