#!/usr/bin/env python3
from osgeo import gdal, ogr, osr
import pandas, geopandas, os, csv, math, numpy, argparse

def shapely_enveloppe(x,y,dx,dy):
    
    # corners coordinates
    ul = (x,      y)      # upper left
    ur = (x + dy, y)      # upper right
    bl = (x,      y + dy) # bottom left
    br = (x + dx, y + dy) # bottom right

    shape = ogr.Geometry(ogr.wkbLinearRing)
    for corner in [ul, bl, br, ur, ul]:
        shape.AddPoint(corner[0], corner[1])
    geom = ogr.Geometry(ogr.wkbPolygon)
    geom.AddGeometry(shape)

    return geom

current_working_directory = os.getcwd()

input_directory = current_working_directory+"/input_data"
output_directory = current_working_directory+"/output_data"

do_write_tiles  = False
do_write_points = False

project_crs = osr.SpatialReference()
project_crs.ImportFromEPSG(2056)

tile_size = 5000.0 # in crs unit

study_area_file = input_directory+"/switzerland.csv"
with open(study_area_file) as study_area:
    study_area_wkt = next(csv.reader(study_area, delimiter=";"))[0]

study_area_crs = osr.SpatialReference()
study_area_crs.ImportFromEPSG(4326)
study_area_crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER) # to correct osr swapping axis

transform = osr.CoordinateTransformation(study_area_crs, project_crs) # reproj from source crs to target crs

study_area_geom = ogr.CreateGeometryFromWkt(study_area_wkt)
study_area_geom.Transform(transform)
study_area_enveloppe = study_area_geom.GetEnvelope()

# xn and yn the number of tiles in each axis
xn = yn = 1/tile_size
xn *= (study_area_enveloppe[1] - study_area_enveloppe[0])
yn *= (study_area_enveloppe[3] - study_area_enveloppe[2])

xn, yn = math.ceil(xn), math.ceil(yn)

driver = gdal.GetDriverByName("GTiff")
reference_dataset = driver.Create(output_directory+"/reference.tif", xn, yn, 1, gdal.GDT_Int16)
reference_dataset.SetProjection(project_crs.ExportToWkt())
reference_dataset.SetGeoTransform([study_area_enveloppe[0], tile_size, 0, study_area_enveloppe[2], 0, tile_size])
reference_dataset.GetRasterBand(1).WriteArray(numpy.random.randint(0,2**4,(yn,xn)))

image_paths = []

images = []
for image_path in image_paths:
    
    image_dataset = gdal.Open(image_path)

    image_crs = osr.SpatialReference(wkt=image_dataset.GetProjection())

    gdal.ReprojectImage(image_dataset, image_path.replace(".tif","_reprojected.tif"),
                        image_crs.ExportToWkt(), project_crs.ExportToWkt,
                        gdal.GRA_Bilinear)

    # align with raster reference
    
    image = {}
    image["dataset"] = image_dataset

if do_write_points:
    points_file = input_directory+"/GPR_points.shp"
    collections_file = input_directory+"/GPR_profiles.shp"
    polygons_file = input_directory+"/SGI_2016_glaciers.shp"

    output_points_directory = output_directory+"/gpr_points"

    points_dataset = geopandas.read_file(points_file)
    collections_dataset = geopandas.read_file(collections_file)
    polygons_dataset = geopandas.read_file(polygons_file)

# /!\ must adjust to each input properties
padding_size_pixel = 2**3 # 2^n with n equal to number of convolution layers in model
tile_resolution = tile_size / (2**8 - padding_size_pixel * 2)
padding_size = padding_size_pixel * tile_resolution

i = 0
for y_tile in range(yn):
    for x_tile in range(xn):

        # coordinates of the upper left corner without padding in crs unit
        x_coordinate = y_coordinate = tile_size
        x_coordinate *= x_tile
        y_coordinate *= y_tile

        # coordinates of the upper left corner with padding in crs unit
        x_padding = y_padding = -padding_size_pixel * tile_resolution
        x_padding += x_coordinate
        y_padding += y_coordinate
        
        for image_file in images:

            image_name = image_file.split("/")[-1].split(".")[0]

            output_directory = output_directory+"/"+image_name
            tile_file = output_directory+"/"+image_name+"_"+str(i)+".tif"

            gdal_translate_string = "gdal_translate -of GTIFF\
                                     -srcwin "+str(x_padding)+", "+str(y_padding)+", "+str(tile_size)+", "+str(tile_size)+" \
                                    "+image_file+" "+tile_file
            os.system(gdal_translate_string)

        if do_write_points:

            tile_geom = shapely_enveloppe(x_coordinate, y_coordinate, tile_size, tile_size)

            polygons_intersected = polygons_dataset.loc[polygons_dataset["geometry"].intersects(tile_geom)]
            
            collections_intersected = collections_dataset.loc[collections_dataset["sgi_id"].isin(polygons_intersected["sgi-id"].str.replace("-","/"))]
            collections_intersected = collections_intersected.loc[collections_intersected["geometry"].intersects(tile_geom)]
            
            points_intersected = points_dataset.loc[points_dataset["prf_name"].isin(collections_intersected["prf_name"])]
            points_intersected = points_intersected.loc[points_intersected["geometry"].intersects(tile_geom)]

            if not points_intersected.empty:
                points_intersected["x"] = points_intersected["geometry"].x
                points_intersected["y"] = points_intersected["geometry"].y
                output_dataframe = pandas.DataFrame(points_intersected.drop('geometry',axis=1))

                output_dataframe = output_dataframe.to_csv(output_points_directory+"/gpr_points_"+str(i)+".csv")

            # write the code for rasterized version

        print(i)

        i += 1



reference_dataset.FlushCache()
reference_dataset = None