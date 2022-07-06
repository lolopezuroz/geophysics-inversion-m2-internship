from numpy import tile
from functions.import_libraries import pandas, math, gdal, numpy, geometry

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

def shapely_enveloppe(x,y,dx,dy):
    """
    create a square enveloppe based on upper corner coordinates and sides
    lengths
    """
    # corners coordinates
    ll = (x,      y)      # lower left
    ur = (x + dx, y + dy) # upper right
    ul = (x,      y + dy) # upper left
    lr = (x + dx, y)      # lower right

    geom = geometry.box(ll[0], ll[1], ur[0], ur[1])
    return geom

def geo_subset(geom, df, df_foreign_key, features_id):
    """
    subset a dataframe "df" by ids from "features_id" and by spatial
    intersection with "geom"
    """
    df_subset = df.loc[df[df_foreign_key].isin(features_id)]
    df_subset = df_subset.loc[df_subset["geometry"].intersects(geom)]

    return df_subset

def export_tile(image_dataset, tile_path, ul, tile_size):

    # in pixel coordinates !!!
    
    gdal_translate_options = gdal.TranslateOptions(srcWin=(ul[0],
                                                           ul[1],
                                                           tile_size,
                                                           tile_size))

    return gdal.Translate(tile_path,
                          image_dataset,
                          options=gdal_translate_options)

def export_geom(geodataframe, output_path):

    # export to csv cant keep geometry as an object
    geodataframe["x"] = geodataframe["geometry"].x
    geodataframe["y"] = geodataframe["geometry"].y
    output_dataframe = geodataframe.drop('geometry',axis=1)
    output_dataframe = pandas.DataFrame(output_dataframe)
    output_dataframe = output_dataframe.to_csv(output_path)

def tile_dataset(images, points_datasets, tile_size, study_area_enveloppe):

    # xn and yn the number of tiles in each axis (not an integer)
    xn = yn = 1/tile_size
    xn *= (study_area_enveloppe[1] - study_area_enveloppe[0])
    yn *= (study_area_enveloppe[3] - study_area_enveloppe[2])

    """
    this extend the enveloppe boundaries from the bottom right corner so it
    include all the study area (become integer)
    """
    xn, yn = math.ceil(xn), math.ceil(yn)

    i = 0
    for y_tile in range(yn):
        for x_tile in range(xn):


            # coordinates of lower left corner without padding in crs unit
            x_coordinate = y_coordinate = tile_size
            x_coordinate *= x_tile
            y_coordinate *= y_tile
            x_coordinate += study_area_enveloppe[0]
            y_coordinate += study_area_enveloppe[2]
            
            print("\tTile",i, x_coordinate, y_coordinate)
            
            for image in images:
                
                padding_size_pixel = image["padding_size_pixel"]
                tile_size_pixel = image["tile_size_pixel"]
                full_size_pixel = image["full_size_pixel"]

                # coordinates of upper left corner with padding in pixels
                x_ul = y_ul = -padding_size_pixel
                x_ul += x_tile * tile_size_pixel
                y_ul += (yn-y_tile-1) * tile_size_pixel # y axis is reverted!!!

                image_array = image["dataset"].ReadAsArray()
                image_size_x, image_size_y = image["size_x"], image["size_y"]

                extent = [max(0,x_ul),min(x_ul+full_size_pixel,image_size_x),
                          max(0,y_ul),min(y_ul+full_size_pixel,image_size_y)]
                extract = image_array[extent[2]:extent[3],extent[0]:extent[1]]
                if not numpy.isnan(extract).all():
                    tile_path = image["output_directory"]+"/"+\
                                image["name"]+"_tile_"+str(i)+".tif"
                    export_tile(image["dataset"],
                                tile_path,
                                (x_ul,y_ul),
                                full_size_pixel)

            for points in points_datasets:

                tile_geom = shapely_enveloppe(x_coordinate, y_coordinate,
                                              tile_size, tile_size)

                geodataframes = [points["dataset"]] + points["containers"]

                if points["containers"]:

                    geodataframe = points["containers"][-1]
                    for following_geodataframe,\
                        geodataframe_primary_key,\
                        following_geodataframe_foreign_key\
                    in zip(geodataframes[1::-1],
                           points["primary_keys"][::-1],
                           points["foreign_keys"][::-1]):

                        intersected_features_ids = geodataframe[geodataframe_primary_key]

                        if following_geodataframe_foreign_key == "sgi_id":
                            intersected_features_ids = intersected_features_ids\
                                                       .str.replace('-','/')

                        geodataframe = geo_subset(tile_geom,
                                                  following_geodataframe,
                                                  following_geodataframe_foreign_key,
                                                  intersected_features_ids)

                if not geodataframe.empty:
                    export_geom(geodataframe,
                                points["output_directory"]+ \
                                "/gpr_points_"+str(i)+".csv")

                # write the code for rasterized version

            i += 1