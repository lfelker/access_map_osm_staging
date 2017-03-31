# Sidewalk Extrapolation

import os
import json
from shapely.geometry import Point, LineString
import pandas as pd
import geopandas as gpd
from geopandas import GeoSeries, GeoDataFrame

import matplotlib.pyplot as plt
import matplotlib
import fiona

# The two statemens below are used mainly to set up a plotting
# default style that's better than the default from matplotlib
import seaborn as sns
plt.style.use('bmh')

json_config = open("config.json").read()
c = json.loads(json_config)

# REMEMBER TO USE PYTHON 3: source py3env/bin/activate

def main():
	swk_network = gpd.read_file(os.path.join(c['data_path'], c['sidewalk_network_shapefile']))
	lr_stations = gpd.read_file(os.path.join(c['data_path'], c['station_shapefile']))

	station_buffers = {}
	for station in c['target_stations']:
		station_buffers[station] = buffer_station(swk_network, lr_stations, station, c['buffer_distance'])

	plot_target_stations(swk_network, lr_stations, station_buffers)

def plot_target_stations(swk_network, lr_stations, station_buffers):
	# retrieve plot_ref so future plot calls can be put on same figure
	plot_ref = lr_stations.plot(marker='*', color='red', markersize=5)
	#swk_network is too large to plot with pyplot
	#swk_network.plot(ax=plot_ref, color='grey', linewidth=0.3)
	#swk_ntwrk.plot(ax=plot_ref, color='grey')
	for station_key in station_buffers.keys():
		station = station_buffers[station_key]
		filter_sidewalks(station).plot(ax=plot_ref, color='blue')
	# labels for stations
	for idx, row in lr_stations.iterrows():
		point = row[c['geometry']]
		coord = (point.x, point.y)
		plt.annotate(s=row['name'], xy=coord, fontsize=8)
	plt.show()

# returns only streets with a sidewalk on at least one side
def filter_sidewalks(df_swks):
	only_swks = df_swks.query(c['swk_left'] + ' == ' + str(c['swk_present']) + ' or ' + c['swk_right'] + ' == ' + str(c['swk_present']))
	return only_swks

#returns dataframe with only swks surrounding station at the specified distance
def buffer_station(swk_ntwrk, stations, station_name, distance):
	station = stations[stations.name == station_name]
	buff = station.buffer(distance).iloc[0]
	intersection = swk_ntwrk.loc[swk_ntwrk.intersects(buff)]
	return intersection

# takes column name of line geometry to sum and column name of sidewalk left and right presence
# Note: sidewalk presence is specified by 1, 0 means absence.
# returns the sum of of all sidewalks in meters
def sum_sidewalks(gdf, sum_row_name):
	sidewalk_sum = 0.0
	for index, row in gdf.iterrows():
		geo = row[sum_row_name]
		road_length = geo.length
		if row[c['swk_left']] == c['swk_present']:
			sidewalk_sum += road_length
		if row[c['swk_right']] == c['swk_present']:
			sidewalk_sum += road_length
	return sidewalk_sum

if __name__ == "__main__":
    main()

