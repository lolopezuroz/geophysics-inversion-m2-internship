from functions.import_libraries import os, math

def exist_directory(path:str) -> str:
    """
    check if "path" represent an existent directory
    if not, it create the full path to it

    path:str

    return:str the path of tested directory
    """
    if not os.path.isdir(path):
        parent_directory = path[:path.rfind("/")]
        exist_directory(parent_directory)
        os.mkdir(path)
    return path

def best_size(resolution:float,tile_size:float) -> int:
    """
    find smaller power of two to use for tile size in pixel
    the use of power of two ensure it remain dividable if resolution
    is doubled or halved

    resolution:float pixel size
    tile_size:float

    return:int
    """
    return 2**int(math.log(tile_size/resolution,2))