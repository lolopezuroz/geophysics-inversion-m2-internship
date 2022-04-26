from functions.import_libraries import osr, gdal, numpy, os

def import_image(image_dataset,
                 tile_size,
                 project_crs,
                 study_area):
    """
    add elements to the image dataset

    image_dataset:dict
        path:str
        output_directory:str
        resolution:float pixel size in project crs units
        padding_size_pixel:int

    tile_size:float
    project_crs:osr.SpatialReference
    
    return image_dataset:dict
    """
    image_raster = gdal.Open(image_dataset["path"])
    image_crs = osr.SpatialReference(wkt=image_raster.GetProjection())

    image_resolution = image_dataset["resolution"]
    padding_size_pixel = image_dataset["padding_size_pixel"]
    padding_size = padding_size_pixel * image_resolution

    # reproject raster into project coordinates reference system
    new_image_path = image_dataset["path"].replace(".tif","_reprojected.tif")
    if not os.path.isfile(new_image_path):
        image_raster = gdal.Warp(new_image_path,image_raster,
                                srcSRS=image_crs.ExportToWkt(),
                                dstSRS=project_crs.ExportToWkt(),
                                resampleAlg=gdal.GRA_Bilinear,
                                multithread=True)
        image_raster.FlushCache() # save changes
    else: image_raster = gdal.Open(new_image_path)

    # crop and align raster with study area
    new_image_path = image_dataset["path"].replace(".tif","_aligned.tif")
    if not os.path.isfile(new_image_path):
        gdal_warp_options = gdal.WarpOptions(xRes=image_resolution,
                                            yRes=image_resolution,
                                            outputBounds=(study_area["x_left"],
                                                        study_area["y_lower"],
                                                        study_area["x_right"],
                                                        study_area["y_upper"]),
                                            dstNodata=numpy.nan,
                                            resampleAlg=gdal.GRA_Average,
                                            multithread=True)
        image_raster = gdal.Warp(new_image_path,
                                image_raster,
                                options=gdal_warp_options)
        image_raster.GetRasterBand(1).SetNoDataValue(numpy.nan)
        image_raster.FlushCache()
    else: image_raster = gdal.Open(new_image_path)

    x0, _, _, y0, _, _  = image_raster.GetGeoTransform()

    tile_size_pixel = tile_size//image_resolution # necessarily whole division

    image_dataset["name"] = image_dataset["path"].split("/")[-1].split(".")[0]
    image_dataset["path"] = new_image_path
    image_dataset["resolution"] = image_resolution
    image_dataset["padding_size"] = padding_size
    image_dataset["tile_size_pixel"] = tile_size_pixel
    image_dataset["full_size_pixel"] = int(tile_size_pixel + padding_size_pixel*2)
    image_dataset["size_x"] = image_raster.RasterXSize
    image_dataset["size_y"] = image_raster.RasterYSize
    image_dataset["x0"] = x0
    image_dataset["y0"] = y0

    del image_raster
    
    return image_dataset