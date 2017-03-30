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

# REMEMBER TO USE PYTHON 3: source py3env/bin/activate

def main(): 
	data_pth = "./ufl_data"
	swk_right = 'kcn_swk__2'
	swk_left = 'kcn_swk__1'
	geometry = 'geometry'

	#trans_network = gpd.read_file(os.path.join(data_pth, "station_sidewalks_subset.shp"))
	#wilburton = trans_network[(trans_network.name == "wilburton")]
	#overlake = trans_network[(trans_network.name == "overlake_villiads")] # mistake on the station name attribute
	#judkins = trans_network[(trans_network.name == "judkins")]

	#wilburton_sidewalk_sum = sum_sidewalks(wilburton, geometry, swk_left, swk_right)
	#print(wilburton_sidewalk_sum)

	#overlake_sidewalk_sum = sum_sidewalks(overlake, geometry, swk_left, swk_right)
	#print(overlake_sidewalk_sum)

	#judkins_sidewalk_sum = sum_sidewalks(judkins, geometry, swk_left, swk_right)
	#print(judkins_sidewalk_sum)

	# Take 2 No QGIS Prep Work
	half_mile = 2640
	swk_ntwrk = gpd.read_file(os.path.join(data_pth, "trans_network_sidewalks.shp"))
	lr_stations = gpd.read_file(os.path.join(data_pth, "light_rail_station_info.shp"))

	wilburton = buffer_station(swk_ntwrk, lr_stations, "wilburton", half_mile)
	overlake = buffer_station(swk_ntwrk, lr_stations, "overlake_villiage", half_mile)
	judkins = buffer_station(swk_ntwrk, lr_stations, "judkins", half_mile)
	sum_w = sum_sidewalks(wilburton, geometry, swk_left, swk_right)
	sum_o = sum_sidewalks(overlake, geometry, swk_left, swk_right)
	sum_j = sum_sidewalks(judkins, geometry, swk_left, swk_right)
	print(sum_w, sum_o, sum_j)

	plot_station(wilburton, lr_stations[lr_stations.name == "wilburton"])

# plots data in each frame
def plot_station(dataframe, station):
	color = "kcn_swk__1"
	ax = dataframe.plot(c=color)
	station.plot(ax=ax)
	plt.show()

#returns dataframe with only swks surrounding station at the specified distance
def buffer_station(swk_ntwrk, stations, station_name, distance):
	station = stations[stations.name == station_name]
	buff = station.buffer(distance).iloc[0]
	intersection = swk_ntwrk.loc[swk_ntwrk.intersects(buff)]
	return intersection

# takes road length and sidewalk left and right data to return the sum of of all sidewalks in meters
def sum_sidewalks(gdf, sum_row_name, swk_left, swk_right):
	sidewalk_sum = 0.0
	for index, row in gdf.iterrows():
		#print(row[sum_row_name], row[swk_left], row[swk_right])
		geo = row[sum_row_name]
		road_length = geo.length
		if row[swk_left] == 1:
			sidewalk_sum += road_length
		if row[swk_right] == 1:
			sidewalk_sum += road_length
	return sidewalk_sum

if __name__ == "__main__":
    main()

