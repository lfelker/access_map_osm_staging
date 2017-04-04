import geopandas

# returns dataframe with only data surrounding station at the specified distance
# Note: the two geodata frames must have the same crs
def buffer_point(point, distance):
	buff = point.buffer(distance).iloc[0]
	return buff

def clip_data(data, buff):
	intersection = data.loc[data.intersects(buff)]
	return intersection

def plot_buffer(data, buff):
	cliped_streets = clip_data(data, buff)
	buffers = []
	buffers.append(buff)
	plot_ref = GeoSeries(buffers).plot()
	cliped_streets.plot(ax=plot_ref)
	plt.show()