import math
from scipy.spatial import Delaunay
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import polygonize_full, linemerge, unary_union
import geopandas as gpd
import pandas as pd

# Read input data
path = 'data/'
f_path = path + 'wd_d_4.shp'
original_points = gpd.read_file(f_path)

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
    return result_df

level_0 = natural_polygons(original_points)
points_l0 = gpd.sjoin(original_points, level_0)

def process_level(points, id_column=None):
    level = []
    if id_column:
        for poly in points[id_column].unique():
            p = points[points[id_column] == poly]
            if p.shape[0] > 50:
                level.append(natural_polygons(p))
        level = pd.concat(level)
    else:
        level = natural_polygons(points)
    return(level)


level_dfs = []
for i in range(3):
    print(i)
    if i == 0:
        last_level = process_level(original_points)
        level_dfs.append(last_level)
    else:
        points = gpd.sjoin(original_points, last_level)
        print(points.columns)
        last_level = process_level(points, 'index_right')
        level_dfs.append(last_level)

for i in range(3):
    print(i)
