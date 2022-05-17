from functions.import_libraries \
import math, gdal, numpy as np

def summarize(extract):

    extract_nanfree = extract[~np.isnan(extract)]

    summary = {}
    summary["fraction_nan"] = np.size(extract_nanfree) / np.size(extract)
    if summary["fraction_nan"] == 0:
        extract_nanfree = [np.nan]
    summary["min"] = np.min(extract_nanfree)
    summary["max"] = np.max(extract_nanfree)
    summary["extent"] = summary["max"] - summary["min"]
    summary["mean"] = np.mean(extract_nanfree)
    summary["std"] = np.std(extract_nanfree)
    summary["median"] = np.median(extract_nanfree)
    summary["cv"] = summary["std"] / summary["mean"]

    return summary

def export_tile(image_raster:gdal.Dataset,
                tile_size:int,
                tile_path:str,
                x_left:int,
                y_upper:int) -> gdal.Dataset:
    """
    extract tile from an image

    image_raster:gdal.Dataset
    tile_size:int size in pixel (padding included)
    tile_path:str
    x_left:int in pixel coordinates
    y_upper:int in pixel coordinates (careful that axis is reverted)

    return:gdal.Dataset the tile extracted from the raster
    """
    
    gdal_translate_options = gdal.TranslateOptions(srcWin=(x_left,
                                                           y_upper,
                                                           tile_size,
                                                           tile_size))

    return gdal.Translate(tile_path,
                          image_raster,
                          options=gdal_translate_options)

def enumerate_x_y(xn:int,yn:int) -> enumerate:
    """
    create an enumerate object to iterate over a grid:
        1st element : cell number
        2sd element : cell column
        3rd element : cell row

    xn:int number of columns
    yn:int number of rows

    return:enumerate
    """
    return enumerate([i%xn, i//xn] for i in range(xn*yn))

def grid_size(study_area:dict,
              tile_spacing:float) -> tuple:
    """
    compute number of tile to extract from study area

    study_area:dict
        x_left:float left bound
        x_right:float right bound
        y_lower:float lower bound
        y_upper:float upper bound
    tile_spacing:float space between each tile

    return:tuple number of columns and number of rows
    """
    xn = (study_area["x_right"] - study_area["x_left"])/tile_spacing
    yn = (study_area["y_upper"] - study_area["y_lower"])/tile_spacing

    xn, yn = math.floor(xn), math.floor(yn)

    return xn, yn

def tile_image(image_dataset:dict,
               study_area:dict,
               tile_size:float,
               tile_spacing:float) -> None:
    """
    split an image into tiles

    image_dataset:dict
        padding_size_pixel:int
        full_size_pixel:int
        size_x:int number of columns
        size_y:int number of rows
        path:str
        resolution:float cell size
        output_directory:str
        name:str
    study_area:dict
        x_left:float left bound
        y_lower:float lower bound
    tile_size:float
    tile_spacing:float

    return:None
    """

    summary = []

    xn, yn = grid_size(study_area,tile_spacing)

    padding_size_pixel = image_dataset["padding_size_pixel"]
    full_size_pixel = image_dataset["full_size_pixel"]

    image_size_x, image_size_y = image_dataset["size_x"],\
                                 image_dataset["size_y"]

    image_raster = gdal.Open(image_dataset["path"])
    image_array = image_raster.ReadAsArray()
    
    for i, [x_tile, y_tile] in enumerate_x_y(xn,yn):

        x_left = study_area["x_left"] + x_tile * tile_spacing
        y_lower = study_area["y_lower"] + y_tile * tile_spacing
        # x_right = x_left + tile_size # not necessary
        y_upper = y_lower + tile_size
        
        x_left_pixel = y_upper_pixel = -padding_size_pixel
        x_left_pixel += int((x_left - study_area["x_left"]) /\
                         image_dataset["resolution"])
        # y axis is reverted !!!
        y_upper_pixel += image_size_y - int((y_upper-study_area["y_lower"])/\
                         image_dataset["resolution"])
        
        extent = [max(0,x_left_pixel) ,
                  min(x_left_pixel +full_size_pixel,image_size_x),
                  max(0,y_upper_pixel),
                  min(y_upper_pixel+full_size_pixel,image_size_y)]

        extract = image_array[extent[2]:extent[3],extent[0]:extent[1]]

        i_summary = summarize(extract)
        i_summary['id']=i
        i_summary['x_left']=x_left
        i_summary['y_lower']=y_lower
        i_summary['present']=i_summary['fraction_nan']!=0

        if i_summary['present'] and np.any(extract != 0):
            tile_path = image_dataset["output_directory"]+"/"+\
                        image_dataset["name"]+"_tile_"+str(i)+".tif"
            export_tile(image_raster,
                        full_size_pixel,
                        tile_path,
                        x_left_pixel,
                        y_upper_pixel)

        summary.append(i_summary)

    return summary

def tile_dataset(image_datasets:list,
                 tile_size:float,
                 tile_spacing:float,
                 study_area:dict) -> None:
    """
    tile a dataset

    return:None
    """

    summaries = {}

    for image_dataset in image_datasets:
        summary = tile_image(image_dataset,study_area,tile_size,tile_spacing)
        summaries[image_dataset['name']] = summary