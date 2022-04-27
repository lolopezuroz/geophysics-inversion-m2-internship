#!/usr/bin/env python3

import sqlalchemy # connect to the database
from osgeo import osr

from functions.import_image import import_image
from functions.import_study_area import import_study_area
from functions.tile_dataset import tile_dataset
from functions.usual_functions import *

from parameters import arguments # parameters of the dataset

def main(args:dict) -> None:
    """
    prepare data and split it into tiles

    args:dict set of parameters
        project_srid:int
        study_area:dict
            path:str path to the csv containing wkt polygon
            srid:int srid of the wkt polygon
        tile_size:float size of a tile in project crs units
        image_datasets:list
            image_dataset:dict
                path:str
                output_directory:str
                resolution:float pixel size in project crs units
                padding_size_pixel:int
        points_datasets:list
            points_dataset:dict
                database:str name of the database in the server
                output_directory:str path where to save the tiles
                tables:list first element is table to split and others are
                "containers" (see tile_dataset.py)
                    table:dict
                        name:str
                        pk:str primary key
                        fk:str foreign key connecting to next container
                        alias:str alias to use in the sql request
                        select:str which columns to extract
                        srid:str srid of geometries

    return None
    """
    # retrieving parameters
    project_srid = args["project_srid"]
    tile_size = args["tile_size"]
    study_area = args["study_area"]
    image_datasets = args["image_datasets"]
    points_datasets = args["points_datasets"]

    # import crs object from srid
    project_crs = osr.SpatialReference()
    project_crs.ImportFromEPSG(project_srid)
    
    print("Importing study area...")

    study_area = import_study_area(study_area,
                                   project_crs)

    print("\tdone")

    for i, image_dataset in enumerate(image_datasets):
        image_dataset = import_image(image_dataset,
                                     tile_size,
                                     project_crs,
                                     study_area)
        exist_directory(image_dataset["output_directory"])
        image_datasets[i] = image_dataset

    for i, points_dataset in enumerate(points_datasets):
        password = "123456789"
        username = "postgres"
        ip = 'localhost'
        url = 'postgresql://'+username+':'+password+'@'+ip+'/'
        url += points_datasets[i]["database"]
        engine = sqlalchemy.create_engine(url)
        exist_directory(points_dataset["output_directory"])
        conn = engine.connect()
        points_datasets[i]["conn"] = conn

    print("Tiling dataset...")
    tile_dataset(image_datasets,points_datasets,tile_size,study_area)
    print("\tdone")
    print("done")

main(arguments)