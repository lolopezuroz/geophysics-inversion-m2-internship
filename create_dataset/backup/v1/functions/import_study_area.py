from functions.import_libraries import osr, csv, ogr

def import_study_area(study_area_path, study_area_crs_int, project_crs_int):
    
    project_crs = osr.SpatialReference()
    project_crs.ImportFromEPSG(project_crs_int)
    
    with open(study_area_path) as study_area:
        study_area_wkt = next(csv.reader(study_area, delimiter=";"))[0]

    study_area_crs = osr.SpatialReference()
    study_area_crs.ImportFromEPSG(study_area_crs_int)

    # magic line to correct osr swapping axis
    study_area_crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

    # reproj from source crs to target crs
    transform = osr.CoordinateTransformation(study_area_crs, project_crs)

    study_area_geom = ogr.CreateGeometryFromWkt(study_area_wkt)
    study_area_geom.Transform(transform) # reproject in crs of project

    study_area = {}
    study_area["geom"] = study_area_geom
    study_area["x_left"], study_area["x_right"], \
    study_area["y_lower"], study_area["y_upper"] = study_area_geom.GetEnvelope()

    return study_area