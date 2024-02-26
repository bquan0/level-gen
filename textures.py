import json

# filenames of all the PBR textures included in game in the textures folder, stored as a dict for each file
texture_folder = "textures"

normal_options = "normal_enabled = true\nnormal_scale = -1.0\n"
depth_options = "depth_enabled = true\ndepth_scale = -0.01\ndepth_deep_parallax = false\ndepth_flip_tangent = false\ndepth_flip_binormal = false\n"

class Texture:
    def __init__(self, folder, jpg_dict, uv1_scale = ""):
        self.folder = folder
        self.jpg_dict = jpg_dict
        # uv shouldn't be in the dict because it doesn't need an ext_resource like the .jpgs
        self.uv1_scale = uv1_scale 


ceiling_tile = Texture(
    folder = "CeilingTile",
    jpg_dict = {
        "albedo" : "OfficeCeiling001_1K-JPG_Color.jpg",
        "roughness" : "OfficeCeiling001_1K-JPG_Roughness.jpg",
        "normal" : "OfficeCeiling001_1K-JPG_NormalGL.jpg", 
        "depth" : "OfficeCeiling001_1K-JPG_Displacement.jpg"
    },
    uv1_scale = "Vector3( 1.5, 1.5, 1 )"
)

plaster = Texture(
    folder = "Plaster",
    jpg_dict = {
        "albedo" : "Plaster001_1K-JPG_Color.jpg",
        "roughness" : "Plaster001_1K-JPG_Roughness.jpg",
        "normal" : "Plaster001_1K-JPG_NormalGL.jpg", 
        "depth" : "Plaster001_1K-JPG_Displacement.jpg"
    },
    uv1_scale = "Vector3( 1.75, 2.25, 1 )"
)

# TODO put in different .json file
tiled_floor = Texture(
    folder = "TiledFloor",
    jpg_dict = {
        "albedo" : "Tiles051_1K-JPG_Color.jpg",
        "roughness" : "Tiles051_1K-JPG_Roughness.jpg",
        "normal" : "Tiles051_1K-JPG_NormalGL.jpg", 
        "depth" : "Tiles051_1K-JPG_Displacement.jpg"
    }
)

# dict of all the textures we already have
texture_dict = {
    "CeilingTile" : ceiling_tile,
    "Plaster" : plaster,
    "TiledFloor" : tiled_floor
}

other_textures = {
    "radioactive": "albedo_color = Color( 0, 1, 0.156863, 1 )\n" + "metallic = 0.3\n" + "roughness = 0.0\n",
    "glass": "flags_transparent = true\n" + "albedo_color = Color( 0.364706, 0.364706, 0.364706, 0.505882 )\n" \
                + "metallic = 1.0\n" + "roughness = 0.0\n"
}

# add textures from a .json file to dict 
# allows contributors to use their own textures (that we don't have)
def add_textures(filename):
    with open(filename, 'r') as f:
        # load JSON object as dictionary
        data = json.load(f)

        textures = data["textures"]
        
        for t in textures:
            # create Texture
            folder = t["folder"]
            jpg_dict = t["jpg_dict"]
            uv1_scale = ""
            if "uv1_scale" in t:
                uv1_scale = t["uv1_scale"]
            texture = Texture(
                folder = folder,
                jpg_dict = jpg_dict,
                uv1_scale = uv1_scale
            )

            # add it to texture_dict
            texture_dict[folder] = texture

# add_textures("input_textures.json")
# for i in texture_dict:
#     print(i)