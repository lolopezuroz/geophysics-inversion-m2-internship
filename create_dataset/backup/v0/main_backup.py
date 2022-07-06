#!/usr/bin/env python3

print("Importing libraries...")

import argparse

from functions.import_image import import_image
from functions.import_points import import_points
from functions.import_study_area import import_study_area
from functions.tile_dataset import tile_dataset
from functions.usual_functions import *

print("\tdone")

def main(args):
    output_directory = args.output_directory

    project_crs_int = args.project_crs

    tile_size = args.tile_size # in crs unit
    padding_size_pixel = args.padding_size_pixel # in pixels

    study_area_path = args.study_area
    study_area_crs_int = args.study_area_crs

    image_paths = args.image_paths if args.image_paths else []
    points_datasets_paths = args.points_datasets if args.points_datasets\
        else []

    geodataframe_primary_keys = args.geodataframe_primary_keys
    geodataframe_foreign_keys = args.geodataframe_foreign_keys

    print("Importing study area...")

    study_area = import_study_area(study_area_path,
                                   study_area_crs_int,
                                   project_crs_int)
    
    # corner coordinates of enveloppe
    study_area_envelope = study_area.GetEnvelope()

    print("\tStudy area extend :",study_area_envelope)

    print("\tdone")

    images = []
    if image_paths:
        print("Importing images...")
        for image_path in image_paths:
            print("\tImporting",image_path,"...")
            image = import_image(image_path,
                                 tile_size,
                                 padding_size_pixel,
                                 project_crs_int,
                                 study_area_envelope)
            image["output_directory"] = \
                exist_directory(output_directory+"/"+image["name"]+"_tiles")
            images.append(image)
            print("\t\tdone")
        print("\tdone")

    

    points_datasets = []
    if points_datasets_paths:
        print("Importing points...")
        i = 0
        for points_dataset_path in points_datasets_paths:
            points = import_points(points_dataset_path,
                                geodataframe_primary_keys[i],
                                geodataframe_foreign_keys[i])
            points["output_directory"] = \
                exist_directory(output_directory+"/"+points["name"]+"_extract")
            points_datasets.append(points)
            print("\t\tdone")
            i += 1
        print("\tdone")
    
    print("Tiling dataset...")
    tile_dataset(images,points_datasets,tile_size,study_area_envelope)
    print("\tdone")

print("Importing parameters...")

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
parser.add_argument("-gpk","--geodataframe_primary_keys",nargs='+',
                    required=False, help="")
parser.add_argument("-gfk","--geodataframe_foreign_keys",nargs='+',
                    required=False,help="")

args = parser.parse_args()

print("\tdone")

main(args)
print("done")