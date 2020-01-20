import argparse
import math
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import MultiPoint, Point, LineString, Polygon
from shapely.ops import polygonize_full, linemerge, unary_union, triangulate
import geopandas as gpd
import pandas as pd

   

# Processing functions
def natural_polygons(points_df, polygon=None):
    """ Take a GeoDataFrame with points and return the natural polygons.

        Parameters:

        points_df (GeoDataFrame): points to process into natural polygons.
        polygon (Polygon GeoDataframe): Single polygon that encloses the points
    """

    tin = triangulate(MultiPoint(points_df.geometry.values), edges=True)
    edges_df = gpd.GeoDataFrame(tin)
    edges_df.rename({0:'geometry'}, axis=1, inplace=True)
    edges_df['length'] = edges_df.geometry.length
    head = edges_df[edges_df['length'] < edges_df.mean(axis=0).length]
    head.crs = {'init': 'epsg:4326'}
    if polygon is not None:
        # use only lines within polygon
        head = gpd.sjoin(head, polygon, how='inner', op='within')

    linework = linemerge(head.geometry.values)
    result, _, _, _ = polygonize_full(linework)
    result = unary_union(result)
    result = {'geometry': result}
    try:
        result_df = gpd.GeoDataFrame(result)
        result_df.crs = {'init': 'epsg:4326'}
    except:
        print(result)
        # return None
        result_df = gpd.GeoDataFrame({'geometry': [result['geometry']]})
        result_df.crs = {'init': 'epsg:4326'}
    return (head, result_df)


def process_level(points, level=None, level_df=None):
    """ Process each level in the hierarchy.

        Parameters:

        points (Point GoDataFrame): Points to process in current level
        level (str): Previous level identifier
        level_df (Polygon GeoDataFrame): Previous level natural polygons

        Returns:

        (Line GeoDataFrame, Polygon GeoDataFrame) current level linework and 
        resulting polygons
    """
    level_polygons = []
    level_lines = []
    # level_points = []
    if level:
        id_field = 'poly_id_' + level  # La columna con los ids del nivel anterior
        for poly in points[id_field].unique():
            p = points[points[id_field] == poly]
            if p.shape[0] > 100:
                polygon = level_df.iloc[[poly]]
                n = natural_polygons(p, polygon)
                if n is not None:
                    if n[0] is not None:
                        lines = n[0]
                        lines['poly_id'] = poly
                        level_lines.append(lines)
                    else:
                        print('Algo salio mal 1')
                        print('level: ', level)
                        print('poly_id: ', poly)
                    level_polygons.append(n[1])
        if len(level_polygons):
            level_lines = pd.concat(level_lines)
            level_polygons = pd.concat(level_polygons)
        else:
            level_lines = None
            level_polygons = None
    else:
        n = natural_polygons(points)
        level_lines = n[0]
        level_polygons = n[1]
    level_polygons.reset_index(inplace=True)
    level_polygons.drop(['index'], axis=1, inplace=True)
    return (level_polygons, level_lines)


def natural_cities(points, depth):
    """ Process points file to obtain natural cities polygons across _depth_ levels.

        Parameters:

        points (Point GeoDataFrame): Points to be aggregated into natural cities.

        depth (int): Number of levels to calculate.

        Returns:

        (Polygon GeoDataFrame, Line GeoDataFrame, Point GeoDataFrame): Resulting 
        natural cities
    """

    # We don't care about attributes so we keep only id
    # Id column name is hardcoded!!!!
    points = points[['id', 'geometry']]
    polygon_levels_list = []
    level_points = []
    lines_level_list = []
    for i in range(depth):
        print("processing level: " + str(i))
        if i == 0:
            this_level = process_level(points)
            level_points = points
            # points = gpd.sjoin(points, this_level[0], how='left', op='within')
            # points.rename(
            #     columns={'index_right': 'poly_id_level_0'}, inplace=True)
            # points['level'] = 'level_0' # Está mal, creo que no importa, Si importa
            print("puntos originales: ", points.shape[0])
        else:
            # Label points with previous level polygons and filter
            level_points = gpd.sjoin(level_points, this_level[0])
            level_points.rename(columns={'index_right': 'poly_id_level_' + str(i-1)},
                                inplace=True)
            print("puntos en este nivel: ", level_points.shape[0])
            this_level = process_level(level_points,
                                       'level_' + str(i-1), this_level[0])
            # if i < depth - 1:
            #     points = gpd.sjoin(points, this_level[0])
            #     points.rename(columns={'index_right': 'poly_id_level_' + str(i)},
            #                   inplace=True)
            #     points['level'] = 'level_' + str(i)
        if this_level[0] is not None:
            print("Number of polygons in level " + str(i) + ": " +
                  str(this_level[0].shape[0]))

            this_level[0]['level'] = 'level_' + str(i)
            this_level[0]['poly_id'] = this_level[0].index  # ???
            polygon_levels_list.append(this_level[0])
            this_level[1]['level'] = 'level_' + str(i)
            # I'm not shure this works (why polygon index should
            # align with lines?):
            # Seguro que esto no es lo mismo
            this_level[1]['poly_id'] = this_level[1].index
            lines_level_list.append(this_level[1])
    polygons = gpd.GeoDataFrame(pd.concat(polygon_levels_list))
    lines = gpd.GeoDataFrame(pd.concat(lines_level_list, sort=True))
    return (polygons, lines)
