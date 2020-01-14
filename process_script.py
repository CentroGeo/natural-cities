import os
import argparse
import geopandas as gpd
from naturalcities import natural_cities

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate Natural Cities\
                                     Polygons')
    parser.add_argument('--input', help="Path to input point shapefile.",
                        default="data/sample.shp")
    parser.add_argument('--out_path', help="Path to output",
                        default="data/output/")
    parser.add_argument('--depth', help="Max Number of hierarchical levels",
                        default=3)

    args = parser.parse_args()
    original_points = gpd.read_file(args.input)
    polygons, lines, points = natural_cities.natural_cities(original_points,
                                                            args.depth)
    polygons.to_file(os.path.join(args.out_path, 'polygons.shp'))
    lines.to_file(os.path.join(args.out_path, 'lines.shp'))
    points.to_file(os.path.join(args.out_path, 'points.shp'))