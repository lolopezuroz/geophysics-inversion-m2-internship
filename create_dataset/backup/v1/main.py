#!/usr/bin/env python3

print("Importing libraries...")

import sqlalchemy

from functions.import_image import import_image
from functions.import_study_area import import_study_area
from functions.tile_dataset import tile_dataset
from functions.usual_functions import *

from parameters import arguments

print("\tdone")

def main(args):
    project_crs_int = args["project_crs"]

    tile_size = args["tile_size"]
    padding_size_pixel = args["padding_size_pixel"]

    study_area_path = args["study_area"]
    study_area_crs_int = args["study_area_crs"]

    image_datasets = args["image_datasets"]
    points_datasets = args["points_datasets"]

    print("Importing study area...")

    study_area = import_study_area(study_area_path,
                                   study_area_crs_int,
                                   project_crs_int)

    print("\tStudy area extend :",study_area["geom"].GetEnvelope())

    print("\tdone")

    for i in range(len(image_datasets)):
        image_dataset = import_image(image_datasets[i],
                                     tile_size,
                                     padding_size_pixel,
                                     project_crs_int,
                                     study_area)
        exist_directory(image_dataset["output_directory"])
        image_datasets[i] = image_dataset

    for i in range(len(points_datasets)):

        engine = sqlalchemy.create_engine('postgresql://postgres:123456789@localhost/'+points_datasets[i]["database"])
        exist_directory(points_datasets[i]["output_directory"])
        conn = engine.connect()
        points_datasets[i]["conn"] = conn

    print("Tiling dataset...")
    tile_dataset(image_datasets,points_datasets,tile_size,study_area)
    print("\tdone")

main(arguments)
print("done")