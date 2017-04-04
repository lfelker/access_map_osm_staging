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

# REMEMBER TO USE PYTHON 3: 
# I found it useful to use a virtualenv for this
# to create: virtualenv -p /usr/bin/python3 py3env
# to activate: source py3env/bin/activate

def main():
	streets_ntwk = gpd.read_file(os.path.join(c['data_path'], c['sidewalk_network_shapefile']))
	lr_stations = gpd.read_file(os.path.join(c['data_path'], c['station_shapefile']))

	station_buffers = {}
	for station in c['target_stations']:
		station_buffers[station] = buffer_station(streets_ntwk, lr_stations, station, c['buffer_distance_feet'])

	#plot_target_stations(swk_network, lr_stations, station_buffers)

	plot_ref = lr_stations.plot(marker='*', color='red', markersize=5)
	for station_key in station_buffers.keys():
		streets = station_buffers[station_key]
		streets.plot(ax=plot_ref, color='grey')
		swks = generate_swks(streets)
		plot_swks(swks, plot_ref)
	plt.show()


# returns geoseries of generated sidewalks within the passes buffers
def generate_swks(streets):
	sidewalks = []
	streets = filter_sidewalks(streets)
	for idx, row in streets.iterrows():
		street = row[c['geometry']]
		col_name = c['st_type_code']
		print(col_name)
		st_type_intermediate = row[col_name]
		st_type = c['st_type'][st_type_intermediate]
		offset = c['st_type_offset'][st_type]
		print(offset)
		if row[c['swk_left']] == c['swk_present']:
			sidewalks.append(street.parallel_offset(offset, 'left', resolution=16, join_style=1, mitre_limit=40.0))
		if row[c['swk_right']] == c['swk_present']:
			sidewalks.append(street.parallel_offset(offset, 'right', resolution=16, join_style=1, mitre_limit=40.0))
	return sidewalks

# hacky way to plot swks to handle size
def plot_swks(swks, plot_ref):
	series_builder = []
	print(type(swks))
	idx = 0
	for sidewalk in swks:
		series_builder.append(sidewalk)
		if idx % 100 == 0:
			GeoSeries(series_builder).plot(ax=plot_ref, color='blue')
			series_builder = []
		idx += 1

def plot_target_stations(swk_network, lr_stations, station_buffers):
	# retrieve plot_ref so future plot calls can be put on same figure
	plot_ref = lr_stations.plot(marker='*', color='red', markersize=5)
	# swk_network is too large to plot with pyplot
	# swk_network.plot(ax=plot_ref, color='grey', linewidth=0.3)
	# swk_ntwrk.plot(ax=plot_ref, color='grey')
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

# returns dataframe with only swks surrounding station at the specified distance
# Note: the two geodata frames must have the same crs
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

