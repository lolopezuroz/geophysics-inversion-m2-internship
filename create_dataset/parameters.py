import os

pwd = os.getcwd() # project working directory

input_directory=pwd+"/input_data"
output_directory=pwd+"/output_data"

project_srid=2056 # (coordinates reference system)

study_area={}
study_area["path"]=input_directory+"/switzerland.txt" # wkt polygon
study_area["srid"]=4326 # coordinates reference system used for poylgon wkt

tile_size=1000.0 # in project coordinates reference system units
tile_spacing=1000.0
# define image datasets

velocity_dataset = {}
velocity_dataset["path"]=input_directory+"/V_RGI-11_2021July01.tif"
velocity_dataset["output_directory"]=output_directory+"/V_RGI-11_2021July01_tiles"
velocity_dataset["resolution"]=50.
velocity_dataset["padding_size_pixel"]=14

dem_dataset = {}
dem_dataset["path"]=input_directory+"/SwissALTI3D_r2019.tif"
dem_dataset["output_directory"]=output_directory+"/SwissALTI3D_r2019_tiles"
dem_dataset["resolution"]=12.5 # or 25.
dem_dataset["padding_size_pixel"]=28

slope_dataset = {}
slope_dataset["path"]=input_directory+"/slope_swissAlti3d.tif"
slope_dataset["output_directory"]=output_directory+"/slope_swissAlti3d"
slope_dataset["resolution"]=12.5 # or 25.
slope_dataset["padding_size_pixel"]=28

thickness_dataset = {}
thickness_dataset["path"]=input_directory+"/IceThickness.tif"
thickness_dataset["output_directory"]=output_directory+"/IceThickness_tiles"
thickness_dataset["resolution"]=12.5
thickness_dataset["padding_size_pixel"]=0

dminus_thickness_dataset = {}
dminus_thickness_dataset["path"]=input_directory+"/IceThicknessUncertaintyMinus.tif"
dminus_thickness_dataset["output_directory"]=output_directory+"/IceThicknessUncertaintyMinus_tiles"
dminus_thickness_dataset["resolution"]=12.5
dminus_thickness_dataset["padding_size_pixel"]=0

dplus_thickness_dataset = {}
dplus_thickness_dataset["path"]=input_directory+"/IceThicknessUncertaintyPlus.tif"
dplus_thickness_dataset["output_directory"]=output_directory+"/IceThicknessUncertaintyPlus_tiles"
dplus_thickness_dataset["resolution"]=12.5
dplus_thickness_dataset["padding_size_pixel"]=0

class_dataset = {}
class_dataset["path"]=input_directory+"/glacier_class.tif"
class_dataset["output_directory"]=output_directory+"/glacier_class"
class_dataset["resolution"]=12.5
class_dataset["padding_size_pixel"]=0

#image_datasets=[velocity_dataset, slope_dataset, thickness_dataset, dminus_thickness_dataset, dplus_thickness_dataset]
image_datasets=[velocity_dataset,class_dataset]

arguments = {}

arguments["project_srid"] = project_srid
arguments["study_area"] = study_area

arguments["tile_size"] = tile_size
arguments["tile_spacing"] = tile_spacing

arguments["image_datasets"] = image_datasets
