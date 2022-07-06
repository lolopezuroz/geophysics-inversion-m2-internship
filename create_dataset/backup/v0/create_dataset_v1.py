import rasterio
from rasterio.mask import mask
from rasterio.warp import Resampling, reproject
import os
import numpy
from shapely import geometry, ops
import geopandas
import pyproj
import pandas

def write_image_as_geo_tiff(dataset, transform, metadata, crs, filename):
    # write dataset as GeoTIFF
    metadata.update({"driver":"GTiff",
                     "height":dataset.shape[1],
                     "width":dataset.shape[2],
                     "transform": transform,
                     "crs": crs})
    with rasterio.open(filename+".tif", "w", **metadata) as destination_file:
        destination_file.write(dataset)

def get_tile(dataset, geom, filename, tile_id):
    # crop dataset using geom and write it out as GeoTIFF
    tile, tile_transform = mask(dataset, [geom], crop=True)

    if not(numpy.isnan(tile).all()): # if not totally empty
        write_image_as_geo_tiff(tile, tile_transform, dataset.meta, dataset.crs, filename+"_"+str(tile_id))

def get_tile_geom(transform, x, y, tile_size):
    # generate bounding box from pixel-wise coordinates
    corner1, corner2 = transform * (x, y), transform * (x + tile_size, y + tile_size) # convert from pixel-wise to geographic-wise
    geom = geometry.box(corner1[0], corner1[1], corner2[0], corner2[1])
    return geom

current_working_directory = os.getcwd()

input_directory = current_working_directory+"/input_data"

image_file = input_directory+"/V_RGI-11_2021July01_warped.tif"
image_file_bis = input_directory+"/V_RGI-11_2021July01.tif"

points_file = input_directory+"/GPR_points.shp"
collections_file = input_directory+"/GPR_profiles.shp"
polygons_file = input_directory+"/SGI_2016_glaciers.shp"

output_path = current_working_directory+"/output"

output_tiles_directory = output_path+"/velocity_tiles"
output_points_directory = output_path+"/gpr_points"
output_tiles_directory_bis = output_path+"/dem_tiles"

tile_size = 2**8
tile_size_bis = tile_size*4
padding_size = 2**3 # equal to number of convolutions in model

points_dataset = geopandas.read_file(points_file)
collections_dataset = geopandas.read_file(collections_file)
polygons_dataset = geopandas.read_file(polygons_file)

#image_projection = pyproj.CRS('EPSG:32632')
#points_projection = pyproj.CRS('EPSG:2056')
#project = pyproj.Transformer.from_crs(image_projection, points_projection, always_xy=True).transform

image_dataset = rasterio.open(image_file, "r")
image_dataset_bis = rasterio.open(image_file_bis, "r")

image_resolution = image_dataset.affine[0]
resampled_image_bis_resolution = image_resolution / (tile_size/tile_size_bis)

image_dataset_bis = image_dataset_bis.read(out_shape=(1,
                                                      int(image_dataset_bis.width),
                                                      int(image_dataset_bis.height)),
                                           resampling=Resampling.average)

image_size_x, image_size_y = image_dataset.width, image_dataset.height

xn, yn = image_size_x-padding_size, image_size_y-padding_size

padlesstile_size = tile_size - 2*padding_size

i = 0
for y in range(-padding_size, yn, padlesstile_size):
    for x in range(-padding_size, xn, padlesstile_size):

        tile_geom = get_tile_geom(image_dataset.transform, x, y, tile_size) # crs of image
        #tile_geom_bis = ops.transform(project, tile_geom) # crs of image bis
        
        get_tile(image_dataset, tile_geom, output_tiles_directory+"/velocity_tile", i)
        

        padless_tile_geom = get_tile_geom(image_dataset.transform, x+padding_size, y+padding_size,padlesstile_size)
        #padless_tile_geom = ops.transform(project, padless_tile_geom)

        polygons_intersected = polygons_dataset.loc[polygons_dataset["geometry"].intersects(padless_tile_geom)]
        
        collections_intersected = collections_dataset.loc[collections_dataset["sgi_id"].isin(polygons_intersected["sgi-id"].str.replace("-","/"))]
        collections_intersected = collections_intersected.loc[collections_intersected["geometry"].intersects(padless_tile_geom)]
        
        points_intersected = points_dataset.loc[points_dataset["prf_name"].isin(collections_intersected["prf_name"])]
        points_intersected = points_intersected.loc[points_intersected["geometry"].intersects(padless_tile_geom)]

        if not points_intersected.empty:
            points_intersected["x"], points_intersected["y"] = points_intersected["geometry"].x, points_intersected["geometry"].y
            pandas.DataFrame(points_intersected.drop('geometry',axis=1)).to_csv(output_points_directory+"/gpr_points_"+str(i)+".csv")

            # write the code for rasterized version

        print(i)

        i += 1