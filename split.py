def task_split(gdf, task):
    '''Task is a polygon, gdf is a GeoDataFrame of raw data.'''
    return gdf.loc[gdf.intersects(task)].copy()
