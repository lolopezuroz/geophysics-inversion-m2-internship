from functions.import_libraries import osr, ogr

def import_study_area(study_area:dict, project_crs:osr.SpatialReference) -> dict:
    """
    add elements to the study_area dictionnary

    study_area:dict
        study_area:dict
        path:str path to the txt containing wkt polygon
        srid:int srid of the wkt polygon
    
    project_crs:osr.SpatialReference

    return study_area:dict
    """

    # suppose that file contain a one-line wkt string
    with open(study_area["path"]) as file:
        study_area_wkt = file.read()

    study_area_crs = osr.SpatialReference()
    study_area_crs.ImportFromEPSG(study_area["srid"])

    # magic line to correct osr swapping axis NOT VERIFIED MAY CAUSE TROUBLES
    study_area_crs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    # reproj from source crs to target crs
    transform = osr.CoordinateTransformation(study_area_crs, project_crs)

    study_area_geom = ogr.CreateGeometryFromWkt(study_area_wkt)
    study_area_geom.Transform(transform) # reproject in crs of project

    study_area["geom"] = study_area_geom
    study_area["crs"] = study_area_crs
    study_area["x_left"], \
    study_area["x_right"], \
    study_area["y_lower"], \
    study_area["y_upper"] = study_area_geom.GetEnvelope()

    return study_area