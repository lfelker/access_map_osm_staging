import os
import json
import shutil
import osm
import geopandas as gpd
from geopandas import GeoSeries, GeoDataFrame

import buffer_logic
import click
import subtasks
import staging

# visualizations for testing intersections
import matplotlib.pyplot as plt
import matplotlib
import fiona


json_config = open("config.json").read()
c = json.loads(json_config)

# prepare data to stage in a 1/2 mile around judkins park station
def main():
	crs = {'init': 'epsg:26910'}

	streets = gpd.read_file('./inputdata/streets.shp')
	
	# extract judkins station and create 1/2 mile buffer
	lr_stations = gpd.read_file(os.path.join(c['data_path'], c['judkins_shapefile'])).to_crs(crs)
	station_name = 'judkins'
	station = lr_stations[lr_stations.name == station_name]

	buff = buffer_logic.buffer_point(station, c['buffer_distance_meters'])

	# Read the data into GeoDataFrames, store in dictionary
	layers = ['sidewalks', 'crossings', 'curbramps']
	layers_gdf = {}
	click.echo('Reading files...')
	for layer in layers:
	    gdf = gpd.read_file(os.path.join('./inputdata/', layer + '.shp'))
	    # Reproject
	    gdf = gdf.to_crs({'init': 'epsg:4326'})
	    layers_gdf[layer] = gdf 

	staging.stage(streets, buff, "judkins", layers_gdf)

if __name__ == "__main__":
    main()