#!/usr/bin/env python3

##############################################################################
print("Importing libraries...")

from osgeo import gdal, ogr, osr
import pandas, os, csv, math, numpy, argparse

from functions.import_image import import_image
from functions.import_points import import_points

print("\tdone")
##############################################################################
print("Defining functions...")

def pad_bounds(bounds,padding_size):
    """
    bounds : (x_min, x_max, y_min, y_max)
    """
    x_min = y_min = -padding_size
    x_min += bounds[0]
    y_min += bounds[2]

    x_max = y_max = padding_size
    x_max += bounds[1]
    y_max += bounds[3]

    return (x_min, x_max, y_min, y_max)

def export_tile(image_path, tile_path, ul, tile_size):

    gdal_translate_string = "gdal_translate -of GTIFF\
                            -projwin "+str(ul[0])+", "+str(ul[1])+", \
                           "+str(tile_size)+", "+str(tile_size)+" \
                           "+image_path+" "+tile_path
    
    os.system(gdal_translate_string)

def export_geom(geodataframe, output_path):

    # export to csv cant keep geometry as an object
    geodataframe["x"] = geodataframe["geometry"].x
    geodataframe["y"] = geodataframe["geometry"].y
    output_dataframe = geodataframe.drop('geometry',axis=1)

    output_dataframe = pandas.DataFrame(output_dataframe)
    output_dataframe = output_dataframe.to_csv(output_path)

def exist_directory(path):
    """
    check if "path" represent an existent directory
    if not, it create the full path to it
    """
    if not os.path.isdir(path):
        parent_directory = path[:path.rfind("/")]
        exist_directory(parent_directory)
        os.mkdir(path)
    return path

def geo_subset(geom, df, df_foreign_key, features_id):
    """
    subset a dataframe "df" by ids from "features_id" and by spatial
    intersection with "geom"
    """
    df_subset = df.loc[df[df_foreign_key].isin(features_id)]
    df_subset = df_subset.loc[df_subset["geometry"].intersects(geom)]

    return df_subset

def shapely_enveloppe(x,y,dx,dy):
    """
    create a square enveloppe based on upper corner coordinates and sides
    lengths
    """
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

print("\tdone")
##############################################################################
print("Retrieving parameters...")

parser = argparse.ArgumentParser()

parser.add_argument("-pc","--project_crs", type=int,required=True,
                    help="")
parser.add_argument("-sa","--study_area",required=True,
                    help="")
parser.add_argument("-sac","--study_area_crs", type=int,required=True,
                    help="")

parser.add_argument("-od","--output_directory",required=False,
                    help="")

parser.add_argument("-ts","--tile_size", type=float,required=True,
                    help="")
parser.add_argument("-psp","--padding_size_pixel", type=int,required=False,
                    help="")

parser.add_argument("-ip","--image_paths",nargs='+',
                    help="")

parser.add_argument("-pd","--points_datasets",nargs='+',required=False,
                    help="")
parser.add_argument("-gpk","--geodataframe_primary_keys",nargs='+',required=False,
                    help="")
parser.add_argument("-gfk","--geodataframe_foreign_keys",nargs='+',required=False,
                    help="")

args = parser.parse_args()

output_directory = args.output_directory

project_crs = osr.SpatialReference()
project_crs.ImportFromEPSG(args.project_crs)

tile_size = args.tile_size # in crs unit
padding_size_pixel = args.padding_size_pixel # in pixels

study_area_path = args.study_area
study_area_crs_int = args.study_area_crs

image_paths = args.image_paths if args.image_paths else []
points_datasets_paths = args.points_datasets if args.points_datasets else []

geodataframe_primary_keys = args.geodataframe_primary_keys
geodataframe_foreign_keys = args.geodataframe_foreign_keys

print("\tdone")
##############################################################################
print("Importing study area...")

with open(study_area_path) as study_area:
    study_area_wkt = next(csv.reader(study_area, delimiter=";"))[0]

study_area_crs = osr.SpatialReference()
study_area_crs.ImportFromEPSG(study_area_crs_int)

# magic line to correct osr swapping axis
study_area_crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

# reproj from source crs to target crs
transform = osr.CoordinateTransformation(study_area_crs, project_crs)

study_area_geom = ogr.CreateGeometryFromWkt(study_area_wkt)
study_area_geom.Transform(transform) # reproject in crs of project

# corner coordinates of enveloppe
study_area_enveloppe = study_area_geom.GetEnvelope() 

# xn and yn the number of tiles in each axis (not an integer)
xn = yn = 1/tile_size
xn *= (study_area_enveloppe[1] - study_area_enveloppe[0])
yn *= (study_area_enveloppe[3] - study_area_enveloppe[2])

"""
this extend the enveloppe boundaries from the bottom right corner so it
include all the study area (become integer)
"""
xn, yn = math.floor(xn), math.floor(yn)

driver = gdal.GetDriverByName("GTiff")

reference_dataset = driver.Create(output_directory+"/reference.tif",
                                  xn, yn, 1, gdal.GDT_Int16)
reference_dataset.SetProjection(project_crs.ExportToWkt())
reference_dataset.SetGeoTransform([study_area_enveloppe[0], tile_size, 0,
                                   study_area_enveloppe[2], tile_size, 0])

tile_ids = numpy.arange(xn*yn).reshape(yn,xn)
reference_dataset.GetRasterBand(1).WriteArray(tile_ids)

print("\tdone")
##############################################################################
print("Importing images...")

print("\tImages to import :",image_paths)

images = []
for image_path in image_paths:
    print("\tImporting",image_path,"...")
    image = import_image(image_path,
                         tile_size,
                         padding_size_pixel,
                         project_crs,
                         study_area_enveloppe)
    image["output_directory"] = exist_directory(output_directory+"/"+image["name"]+"_tiles")
    images.append(image)
    print("\t\tdone")

print("\tdone")
##############################################################################
print("Importing points...")

print("\tPoints to import :",points_datasets_paths)

i = 0
points_datasets = []
for points_dataset_path in points_datasets_paths:
    points = import_points(points_dataset_path,
                           geodataframe_primary_keys[i],
                           geodataframe_foreign_keys[i])
    points["output_directory"] = exist_directory(output_directory+"/"+points["name"])
    points_datasets.append(points)
    print("\t\tdone")
    i += 1

print("\tdone")
##############################################################################
print("Tiling dataset...")

i = 0
for y_tile in range(yn):
    for x_tile in range(xn):

        print("\tTile",i)

        # coordinates of the upper left corner without padding in crs unit
        x_coordinate = y_coordinate = tile_size
        x_coordinate *= x_tile
        y_coordinate *= y_tile
        
        for image in images:
            
            padding_size = image["padding_size"]

            # coordinates of the upper left corner with padding in crs unit
            x_padding = y_padding = -padding_size
            x_padding += x_coordinate
            y_padding += y_coordinate

            tile_path = image["output"]+"_"+str(i)+".tif"
            export_tile(image["path"],tile_path,(x_padding,y_padding),
                        tile_size+padding_size*2)

        for points_dataset in points_datasets:

            tile_geom = shapely_enveloppe(x_coordinate, y_coordinate,
                                          tile_size, tile_size)

            geodataframes = [points_dataset["dataset"]]\
                           + points_dataset["containers"]

            geodataframe_subset = geodataframes[-1]
            for geodataframe, \
                geodataframe_primary_key, \
                geodataframe_foreign_key \
            in zip(geodataframes[::-1], \
                   points_dataset["primary_keys"][::-1], \
                   points_dataset["foreign_keys"][::-1]):

                intersected_features_ids = \
                geodataframe_subset[geodataframe_primary_key]

                if geodataframe_foreign_key == "prf_name":
                    intersected_features_ids = intersected_features_ids\
                                               .str.replace('-','/')

                geodataframe_subset = geo_subset(tile_geom,
                                                 geodataframe,
                                                 geodataframe_foreign_key,
                                                 intersected_features_ids)

            if not geodataframe_subset.empty:
                export_geom(geodataframe_subset,
                            points_dataset["output_directory"]+ \
                            "/gpr_points_"+str(i)+".csv")

            # write the code for rasterized version

        i += 1

print("\tdone")
##############################################################################
print("done")