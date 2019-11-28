import argparse
import math
from scipy.spatial import Delaunay
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import polygonize_full, linemerge, unary_union
import geopandas as gpd
import pandas as pd


# Processing functions
def natural_polygons(points_df):
    """Take a GeoDataFrame with points and return the natural polygons."""
    coords = list(zip(points_df.geometry.x.values, points_df.geometry.y.values))
    TIN = Delaunay(coords)
    # list of coordinates for each edge
    edges = []
    for tr in TIN.simplices:
        for i in range(3):
            edge_idx0 = tr[i]
            edge_idx1 = tr[(i+1) % 3]
            edges.append(LineString((Point(TIN.points[edge_idx0]),
                                    Point(TIN.points[edge_idx1]))))

    edges = {'geometry':edges}
    edges_df = gpd.GeoDataFrame(edges)
    edges_df['length'] = edges_df.geometry.length
    head = edges_df[edges_df['length'] < edges_df.mean(axis=0).length]
    linework = linemerge(head.geometry.values)
    linework = unary_union(linework)
    result, _, _, _ = polygonize_full(linework)
    result = unary_union(result)
    result = {'geometry':result}
    result_df = gpd.GeoDataFrame(result)
    result_df.crs = {'init':'epsg:4326'}
    return (edges_df['length'], result_df)

def process_level(points, id_column=None):
    level = []
    if id_column:
        print(points[id_column].unique())
        for poly in points[id_column].unique():
            p = points[points[id_column] == poly]
            if p.shape[0] > 500:
                level.append(natural_polygons(p)[1])
        if len(level):
            level = pd.concat(level)
        else:
            level = None
    else:
        level = natural_polygons(points)[1]
    return level

def natural_cities(base_points, depth):
    level_dfs = []
    for i in range(depth):
        if i == 0:
            last_level = process_level(base_points)
            points = base_points
        else:
            points = gpd.sjoin(points, last_level)
            points.rename(columns={'index_right': 'last_id' + str(i)},
                        inplace=True)
            last_level = process_level(points, 'last_id' + str(i))
        if last_level is not None:
            last_level['level'] = 'level_' +  str(i)
            last_level['poly_id'] = last_level.index
            level_dfs.append(last_level)

    return gpd.GeoDataFrame(pd.concat(level_dfs))
    


