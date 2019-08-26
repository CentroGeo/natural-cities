import psycopg2 as ps

conn = ps.connect("dbname=osm_centro user=postgres password=postgres host=localhost")

def calculate_level(conn):

    cur = conn.cursor()

    ## Create temp table with delaunay edges and lengths

    drop_qry = 'drop table if exists "temp_delaunay";'
    cur.execute(drop_qry)
    conn.commit()

    sql = """create table temp_delaunay as 
    (
        select (st_dump(st_delaunaytriangles(st_collect(the_geom),0.0000001, 1))).path[1] as id, 
        (st_dump(st_delaunaytriangles(st_collect(the_geom),0.0000001, 1))).geom,
        st_length((st_dump(st_delaunaytriangles(st_collect(the_geom),0.0000001, 1))).geom::geography) as length
        from planet_osm_roads_vertices_pgr
    )
    """

    cur.execute(sql)
    conn.commit()

    ## Polygonize and simplify (dissolve). Sore the result in a table
    drop_qry = 'drop table if exists "temp_polygons_0"'
    cur.execute(drop_qry)
    conn.commit()

    sql = """
    create table temp_polygons_0 as 
    with a as (
    select st_exteriorring((st_dump(ST_Union(geom))).geom) as geom
    FROM (select (st_dump(st_polygonize(geom))).path[1] as id, (st_dump(st_polygonize(geom))).geom
    from(
        select * from del_lines 
        where length < ALL(select avg(length) from del_lines)
    ) as foo) as bar
    )
    select (row_number() over())::integer as id, st_makepolygon(geom)  as geom
    from a
    """
    cur.execute(sql)
    conn.commit()