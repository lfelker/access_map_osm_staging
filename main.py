# This is a hacky file meant to represent our initail import - just the
# U district
import geopandas as gpd
import subtasks
import os
import shutil
import json
import osm


crs = {'init': 'epsg:26910'}
# Get the streets shapefile
streets = gpd.read_file('./inputdata/streets.shp').to_crs(crs)

# Isolate blocks
blocks = subtasks.blocks_subtasks(streets)

# Get the neighborhoods
neighborhoods = gpd.read_file('./neighborhoods/Neighborhoods.shp')

# Reproject to common projection
neighborhoods = neighborhoods.to_crs(crs)

# Restrict to the blocks within the neighborhood
mask = neighborhoods['S_HOOD'] == 'University District'
udistrict = neighborhoods.loc[mask, 'geometry'].iloc[0]

tasks = subtasks.filter_blocks_by_poly(blocks, udistrict)

tasks.crs = crs
tasks = tasks.to_crs({'init': 'epsg:4326'})

# FIXME: create real URLs + real chunked data here
tasks['url'] = 'https://testurl.com/' + tasks['poly_id'].astype(str)

udistrict_path = ('./output/udistrict_task.geojson')
if os.path.exists(udistrict_path):
    os.remove(udistrict_path)
tasks.to_file(udistrict_path, driver='GeoJSON')

# Prepare output directory
tasks_path = './output/tasks'
if os.path.exists(tasks_path):
    shutil.rmtree(tasks_path)
os.mkdir(tasks_path)

# Load source data, project, and split into tasks
layers = ['sidewalks', 'crossings', 'curbramps']
layers_gdf = {}

json_list = []
# Read the data into GeoDataFrames, store in dictionary
for layer in layers:
    gdf = gpd.read_file(os.path.join('./inputdata/', layer + '.shp'))
    # Reproject
    gdf = gdf.to_crs({'init': 'epsg:4326'})
    layers_gdf[layer] = gdf

# Split into tasks, validate, and convert to OSM XML.
for idx, task in tasks.iterrows():
    task_dirname = os.path.join(tasks_path, str(task['poly_id']))
    task_path = os.path.join(task_dirname, layer + '.geojson')

    if not os.path.exists(task_dirname):
        os.mkdir(task_dirname)

    data = gdf.loc[gdf.intersects(task.geometry)].copy()

    if not data.shape[0]:
        # There were no features of this layer in the task polygon. Write
        # an empty GeoJSON file
        empty = {
            'type': 'FeatureCollection',
            'features': []
        }
        with open(task_path, 'w') as f:
            json.dump(empty, f)
        continue

    data['poly_id'] = task['poly_id']
