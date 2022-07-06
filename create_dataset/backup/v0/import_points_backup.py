from functions.import_libraries import geopandas

def import_points(points_dataset_path,
                  geodataframe_primary_keys,
                  geodataframe_foreign_keys):

    geodataframe_paths = points_dataset_path.split(",")
    """
    geodataframe contain geodataframe path to tile but also container
    geodataframes
    """
    point_dataset_path = geodataframe_paths[0]
    geodataframe = geopandas.read_file(point_dataset_path)
    
    points_name = point_dataset_path.split("/")[-1].split(".")[0]

    points = {}
    points["name"] = points_name
    points["dataset"] = geodataframe
    points["primary_keys"] = geodataframe_primary_keys.split(',')
    points["foreign_keys"] = geodataframe_foreign_keys.split(',')

    # containers help clustering data to intersect more efficiently
    container_geodataframes = []
    for container_geodataframe_path in geodataframe_paths[1:]:
        container_geodataframe = geopandas.read_file(container_geodataframe_path)
        container_geodataframes.append(container_geodataframe)
    points["containers"] = container_geodataframes

    return points