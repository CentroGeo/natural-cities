import argparse
import geopandas as gpd
from naturalcities import natural_cities

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate Natural Cities\
                                     Polygons')
    parser.add_argument('--input', help="Path to input point shapefile.",
                        default="data/osm_nodes.shp")
    parser.add_argument('--output', help="Path to outfile",
                        default="data/result.shp")
    parser.add_argument('--depth', help="Max Number of hierarchical levels",
                        default=3)

    args = parser.parse_args()
    original_points = gpd.read_file(args.input)
    result = natural_cities.natural_cities(original_points,args.depth)
    result.to_file(args.output)

