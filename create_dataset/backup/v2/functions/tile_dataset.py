from functions.import_libraries \
import pandas, math, gdal, numpy, geometry, geopandas

def geo_subset_sql(tables:list, geom:geometry.Polygon) -> str:
    """
    create sql query to import points intersected by given geometry

    tables:list
        first element is the table to subset
        others are tables whose elements contain the elements from previous
        table and are linked to them by their foreign keys
    geom:geometry.Polygon

    return:str the query to send to the database
    """

    sql =  "SELECT "+tables[0]["select"]+" "
    sql += "FROM "+tables[0]["name"]+" as "+tables[0]["alias"]+" "

    if tables[1:]: # join table to its container
        sql += "INNER JOIN ( "
        sql += geo_subset_sql(tables[1:],geom)
        sql += ") as A ON "+tables[0]["alias"]+"."+tables[0]["fk"]+" = "
        sql += "A."+tables[1]["pk"]+" "
    
    sql += "WHERE ST_Intersects(ST_GeomFromText('"+geom+"',"
    sql += tables[0]["srid"]+"),"+tables[0]["alias"]+".geom)"

    return sql

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

def export_geom(geodataframe:geopandas.GeoDataFrame, output_path:str) -> None:
    """
    save given geodataframe as csv

    geodataframe:geopandas.GeoDataFrame
    output_path:str where to save

    return:None
    """
    
    # column geom is not understood by to_csv
    ### turn this into WKT instead !!!!
    geodataframe["x"] = geodataframe["geom"].x
    geodataframe["y"] = geodataframe["geom"].y
    output_dataframe = geodataframe.drop('geom',axis=1)

    output_dataframe = pandas.DataFrame(output_dataframe)
    output_dataframe = output_dataframe.to_csv(output_path)

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

def grid_size(study_area:dict, tile_size:float) -> tuple:
    """
    compute number of tile to extract from study area

    study_area:dict
        x_left:float left bound
        x_right:float right bound
        y_lower:float lower bound
        y_upper:float upper bound
    tile_size:float

    return:tuple number of columns and number of rows
    """

    xn = yn = 1/tile_size
    xn *= (study_area["x_right"] - study_area["x_left"])
    yn *= (study_area["y_upper"] - study_area["y_lower"])

    xn, yn = math.floor(xn), math.floor(yn)

    return xn, yn

def tile_bounds(x_tile:int,y_tile:int,study_area:dict, tile_size:float):
    """
    find the bound of a tile from its position and size

    x_tile:int tile column
    y_tile:int tile row
    study_area:dict
        x_left:float left bound
        y_lower:float lower bound
    tile_size:float

    return:dict
    """

    x_left = y_lower = tile_size
    x_left *= x_tile
    y_lower *= y_tile
    x_left += study_area["x_left"]
    y_lower += study_area["y_lower"]

    x_right = y_upper = tile_size
    x_right += x_left
    y_upper += y_lower

    bounds = {"x_right":x_right, "y_upper":y_upper,
              "x_left":x_left,   "y_lower":y_lower}

    return bounds

def tile_image(image_dataset:dict, study_area:dict, tile_size:float) -> None:
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

    return:None
    """
    xn, yn = grid_size(study_area,tile_size)

    padding_size_pixel = image_dataset["padding_size_pixel"]
    full_size_pixel = image_dataset["full_size_pixel"]

    image_size_x, image_size_y = image_dataset["size_x"],\
                                 image_dataset["size_y"]

    image_raster = gdal.Open(image_dataset["path"])
    image_array = image_raster.ReadAsArray()
    
    for i, [x_tile, y_tile] in enumerate_x_y(xn,yn):


        tile_i_bounds = tile_bounds(x_tile,y_tile,study_area,tile_size)
        x_left, y_upper = tile_i_bounds["x_left"], tile_i_bounds["y_upper"]
        
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
        if not numpy.isnan(extract).all():
            tile_path = image_dataset["output_directory"]+"/"+\
                        image_dataset["name"]+"_tile_"+str(i)+".tif"
            export_tile(image_raster,
                        full_size_pixel,
                        tile_path,
                        x_left_pixel,
                        y_upper_pixel)

def tile_points(points_dataset:dict,
                study_area:dict,
                tile_size:float) -> None:
    """
    split set of points into tiles

    points_dataset:dict
        tables:list table to split and containers
        conn:_engine.Connect() connection to database
        output_directory:str
    study_area:dict
        x_left:float left bound
        y_lower:float lower bound
    tile_size:float

    return:None
    """

    xn, yn = grid_size(study_area,tile_size)
    
    for i, [x_tile, y_tile] in enumerate_x_y(xn,yn):

        tile_i_bounds = tile_bounds(x_tile,y_tile,study_area,tile_size)
        x_left, x_right, y_upper, y_lower = tile_i_bounds["x_left"],\
                                            tile_i_bounds["x_right"],\
                                            tile_i_bounds["y_upper"],\
                                            tile_i_bounds["y_lower"]

        tile_geom = geometry.box(x_left, y_lower, x_right, y_upper)

        sql = geo_subset_sql(points_dataset["tables"], tile_geom.wkt)

        GeoDF = geopandas.GeoDataFrame
        geodataframe = GeoDF.from_postgis(sql,points_dataset["conn"])
        if not geodataframe.empty:
            export_geom(geodataframe,
                        points_dataset["output_directory"]+\
                        "/gpr_points_"+str(i)+".csv")

def tile_dataset(image_datasets:list,
                 points_datasets:list,
                 tile_size:float,
                 study_area:dict) -> None:
    """
    tile a dataset

    return None
    """

    for image_dataset in image_datasets: tile_image(image_dataset, study_area, tile_size)
    for points_dataset in points_datasets: tile_points(points_dataset, study_area, tile_size)