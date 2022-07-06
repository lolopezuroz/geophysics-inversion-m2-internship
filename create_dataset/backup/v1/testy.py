def query(tables, geom):

    sql = "SELECT "+",".join(tables[0]["select"])+" FROM "+tables[0]["name"]+" as "+tables[0]["alias"]+ " "

    if tables[1:]:
        sql += "INNER JOIN ( "
        sql += query(tables[1:],geom)
        sql += ") as A ON "+tables[0]["alias"]+"."+tables[0]["fk"]+" = A."+tables[1]["pk"] +" "
    
    sql += "WHERE ST_Intersects("+geom+", "+tables[0]["alias"]+".geom)"

    return sql

tables = [
          {"name":'dataset."GPR_points"'       ,"pk":"NONE"    ,"fk":"prf_name", "alias":"pts", "select":["pts.*"]},
          {"name":'dataset."GPR_profiles"'     ,"pk":"prf_name","fk":"sgi_id"  , "alias":"prf", "select":["prf.prf_name"]},
          {"name":'dataset."SGI_2016_glaciers"',"pk":"sgi_id"  ,"fk":"NONE"    , "alias":"glc", "select":["glc.sgi_id"]}
         ]
geom = "ST_GeomFromText( 'POLYGON((2666232 1171432 , 2678747 1171432 , 2678747 1159429 , 2666232 1159429 , 2666232 1171432))',2056)"
print(query(tables,geom))