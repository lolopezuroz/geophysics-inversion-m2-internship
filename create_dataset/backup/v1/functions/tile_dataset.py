from numpy import tile
from functions.import_libraries import pandas, math, gdal, numpy, geometry, geopandas
from functions.usual_functions import exist_directory

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

def geo_subset_sql(tables, geom):

    sql =  "SELECT "+tables[0]["select"]+" "
    sql += "FROM "+tables[0]["name"]+" as "+tables[0]["alias"]+" "

    if tables[1:]:
        sql += "INNER JOIN ( "
        sql += geo_subset_sql(tables[1:],geom)
        sql += ") as A ON "+tables[0]["alias"]+"."+tables[0]["fk"]+" = "
        sql += "A."+tables[1]["pk"]+" "
    
    sql += "WHERE ST_Intersects( ST_GeomFromText('"+geom+"',"+tables[0]["srid"]+"), "+tables[0]["alias"]+".geom)"

    return sql

def export_tile(image, tile_path, x_left, y_upper):

    tile_size = image["full_size_pixel"]
    
    # in pixel coordinates !!!
    gdal_translate_options = gdal.TranslateOptions(srcWin=(x_left,
                                                           y_upper,
                                                           tile_size,
                                                           tile_size))

    return gdal.Translate(tile_path,
                          image["dataset"],
                          options=gdal_translate_options)

def export_geom(geodataframe, output_path):

    # export to csv cant keep geometry as an object
    geodataframe["x"] = geodataframe["geom"].x
    geodataframe["y"] = geodataframe["geom"].y
    output_dataframe = geodataframe.drop('geom',axis=1)
    output_dataframe = pandas.DataFrame(output_dataframe)
    output_dataframe = output_dataframe.to_csv(output_path)

def tile_dataset(images, points_datasets, tile_size, study_area):

    # xn and yn the number of tiles in each axis (not an integer)
    xn = yn = 1/tile_size
    xn *= (study_area["x_right"] - study_area["x_left"])
    yn *= (study_area["y_upper"] - study_area["y_lower"])

    xn, yn = math.floor(xn), math.floor(yn)

    i = 0
    for y_tile in range(yn):
        for x_tile in range(xn):

            # coordinates of lower left corner without padding in crs unit
            x_left = y_lower = tile_size
            x_left *= x_tile
            y_lower *= y_tile
            x_left += study_area["x_left"]
            y_lower += study_area["y_lower"]

            x_right = y_upper = tile_size
            x_right += x_left
            y_upper += y_lower
            

            tile_geom = geometry.box(x_left, y_lower, x_right, y_upper)
            
            for image in images:
                
                padding_size_pixel = image["padding_size_pixel"]
                full_size_pixel = image["full_size_pixel"]

                image_size_x, image_size_y = image["size_x"], image["size_y"]
                
                # coordinates of upper left corner with padding in pixels
                x_left_pixel = y_upper_pixel = -padding_size_pixel
                x_left_pixel += int((x_left - study_area["x_left"]) / image["resolution"])
                y_upper_pixel += image_size_y - int((y_upper - study_area["y_lower"]) / image["resolution"])

                image_array = image["dataset"].ReadAsArray()

                extent = [max(0,x_left_pixel),min(x_left_pixel+full_size_pixel,image_size_x),
                          max(0,y_upper_pixel),min(y_upper_pixel+full_size_pixel,image_size_y)]
                extract = image_array[extent[2]:extent[3],extent[0]:extent[1]]
                if not numpy.isnan(extract).all():
                    tile_path = image["output_directory"]+"/"+\
                                image["name"]+"_tile_"+str(i)+".tif"
                    export_tile(image,tile_path,x_left_pixel,y_upper_pixel)
            
            print("\tTile",i, x_left, y_lower, x_left_pixel, y_upper_pixel)

            for points_dataset in points_datasets:
                sql = geo_subset_sql(points_dataset["tables"], tile_geom.wkt)
                geodataframe = geopandas.GeoDataFrame.from_postgis(sql, points_dataset["conn"])
                if not geodataframe.empty:
                    export_geom(geodataframe,
                                points_dataset["output_directory"]+ \
                                "/gpr_points_"+str(i)+".csv")

                # write the code for rasterized version

            i += 1