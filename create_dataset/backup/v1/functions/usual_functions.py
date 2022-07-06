from functions.import_libraries import os

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

def modulo_round_up(n,modulo):
    return modulo * (n// modulo) + modulo