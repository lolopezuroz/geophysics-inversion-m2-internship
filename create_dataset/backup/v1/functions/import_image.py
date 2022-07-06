from functions.import_libraries import osr, gdal, math, numpy

def ideal_size(resolution,tile_size):
    return 2**int(math.log(tile_size/resolution,2))

def import_image(image_dataset,
                 tile_size,
                 padding_size_pixel,
                 project_crs_int,
                 study_area):

    project_crs = osr.SpatialReference()
    project_crs.ImportFromEPSG(project_crs_int)

    """
    (size = side length of the square tile)
    
    tile_size : size of tile in main crs units (usually meters)
    tile_size_pixel : size of tile in pixels
    
    padding_size : length of padding added to a tile size in main crs units
    padding_size_pixel : length of padding added to a tile size in pixels
    
    image_resolution : size of a pixel in main crs units (usually meters)
    """
    new_image_path = image_dataset["path"].replace(".tif","_reprojected.tif")
    image_raster = gdal.Open(image_dataset["path"])
    image_crs = osr.SpatialReference(wkt=image_raster.GetProjection())
    image_raster = gdal.Warp(new_image_path,image_raster,
                             srcSRS=image_crs.ExportToWkt(),
                             dstSRS=project_crs.ExportToWkt(),
                             resampleAlg=gdal.GRA_Bilinear,
                             multithread=True)
    image_raster.FlushCache()

    _, x_res, _, _, _, y_res  = image_raster.GetGeoTransform()

    tile_size_pixel = ideal_size(max(x_res,y_res), # a power of two idally
                                     tile_size)
    image_resolution = tile_size / (tile_size_pixel)
    padding_size = padding_size_pixel * image_resolution

    new_image_path = new_image_path.replace(".tif","_aligned.tif")
    gdal_warp_options = gdal.WarpOptions(xRes=image_resolution,
                                         yRes=image_resolution,
                                         outputBounds=(study_area["x_left"],
                                                       study_area["y_lower"],
                                                       study_area["x_right"],
                                                       study_area["y_upper"]),
                                         dstNodata=numpy.nan,
                                         resampleAlg=gdal.GRA_Med,
                                         multithread=True)

    image_raster = gdal.Warp(new_image_path,
                              image_raster,
                              options=gdal_warp_options)
    image_raster.GetRasterBand(1).SetNoDataValue(numpy.nan)
    image_raster.FlushCache()

    x0, _, _, y0, _, _  = image_raster.GetGeoTransform()

    image_dataset["name"] = image_dataset["path"].split("/")[-1].split(".")[0]
    image_dataset["path"] = new_image_path
    image_dataset["dataset"] = image_raster
    image_dataset["resolution"] = image_resolution
    image_dataset["padding_size"] = padding_size
    image_dataset["padding_size_pixel"] = padding_size_pixel
    image_dataset["tile_size_pixel"] = tile_size_pixel
    image_dataset["full_size_pixel"] = tile_size_pixel + padding_size_pixel*2
    image_dataset["size_x"] = image_raster.RasterXSize
    image_dataset["size_y"] = image_raster.RasterYSize
    image_dataset["x0"] = x0
    image_dataset["y0"] = y0

    return image_dataset