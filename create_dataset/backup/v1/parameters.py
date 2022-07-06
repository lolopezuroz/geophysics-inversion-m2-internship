import os

pwd = os.getcwd()

input_directory=pwd+"/input_data"
output_directory=pwd+"/output_data"

project_crs=2056

study_area="switzerland.csv"
study_area=input_directory+"/"+study_area
study_area_crs=4326

tile_size=10000.0
padding_size_pixel=2

# define image datasets

# first dataset
velocity_dataset = {}
velocity_dataset["path"]=input_directory+"/V_RGI-11_2021July01.tif"
velocity_dataset["output_directory"]=output_directory+"/V_RGI-11_2021July01_tiles"
velocity_dataset["resolution"]=50.

# second dataset
dem_dataset = {}
dem_dataset["path"]=input_directory+"/SwissALTI3D_r2019.tif"
dem_dataset["output_directory"]=output_directory+"/SwissALTI3D_r2019_tiles"
dem_dataset["resolution"]=12.5

image_datasets=[velocity_dataset, dem_dataset]

# define points datasets

# first dataset
gpr_points = {}
gpr_points["name"]='dataset."GPR_points"'
gpr_points["pk"]="id"
gpr_points["fk"]="prf_name"
gpr_points["alias"]="pts"
gpr_points["select"]="pts.*"
gpr_points["srid"]="2056"

gpr_profiles = {}
gpr_profiles["name"]='dataset."GPR_profiles"'
gpr_profiles["pk"]="prf_name"
gpr_profiles["fk"]="sgi_id"
gpr_profiles["alias"]="prf"
gpr_profiles["select"]="prf.prf_name"
gpr_profiles["srid"]="2056"

glaciers = {}
glaciers["name"]='dataset."SGI_2016_glaciers"'
glaciers["pk"]="sgi_id"
glaciers["fk"]="NONE"
glaciers["alias"]="glc"
glaciers["select"]="glc.sgi_id"
glaciers["srid"]="2056"

gpr_dataset = {}
gpr_dataset["database"]="geophysic_inversion"
gpr_dataset["tables"]=[gpr_points, gpr_profiles, glaciers]
gpr_dataset["output_directory"]=output_directory+"/GPR_points_tiles"

points_datasets=[gpr_dataset]

arguments = {}

arguments["project_crs"] = project_crs
arguments["study_area"] = study_area
arguments["study_area_crs"] = study_area_crs

arguments["tile_size"] = tile_size
arguments["padding_size_pixel"] = padding_size_pixel

arguments["points_datasets"] = points_datasets
arguments["image_datasets"] = image_datasets