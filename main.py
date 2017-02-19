# This is a hacky file meant to represent our initail import - just the
# U district
import geopandas as gpd
import subtasks
import os
import shutil
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
base_url = 'https://import.opensidewalks.com'
city = 'seattle'
neighborhood = 'University_District'
folder = os.path.join(base_url, city, neighborhood)
poly_ids = tasks['poly_id'].astype(str)
tasks['url'] = folder + '/' + poly_ids + '/' + 'University_District-' + \
               poly_ids + '.osm'

udistrict_path = ('./output/University_District.geojson')
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
print 'Reading files...'
for layer in layers:
    gdf = gpd.read_file(os.path.join('./inputdata/', layer + '.shp'))

    # Reproject
    gdf = gdf.to_crs({'init': 'epsg:4326'})

    # Rename columns + column values to be OSM-compatible
    if layer == 'sidewalks':
        # FIXME: Extract width value from SDOT?
        gdf = gdf[['geometry']]
        gdf['highway'] = 'footway'
        gdf['footway'] = 'sidewalk'
    elif layer == 'crossings':
        # FIXME: see if more info can be extracted, as these should be the
        # values used:
        #   1) For a marked crossing with no light signals, use
        #      crossing=uncontrolled
        #   2) For crossings with a traffic signal, do crossing=traffic_signals
        #   3) Technically, we could use crossing=zebra to mirror iD.
        #      Unfortunately, the iD and the wiki disagree about how to mark
        #      crossings.
        gdf = gdf[['geometry']]
        gdf['highway'] = 'footway'
        gdf['footway'] = 'crossing'
        gdf['crossing'] = 'zebra'
    elif layer == 'curbramps':
        gdf = gdf[['geometry']]
        gdf['kerb'] = 'lowered'
        # FIXME: see if we can extract tactile paving info from dataset
        # If so, uncomment below (and add logic)
        # gdf['tactile_paving'] = 'yes'
        # TODO: consider adding barrier=kerb in as many locations as possible.
        # Use of barrier=kerb should be supplemented with kerb height
        # measurement.

    layers_gdf[layer] = gdf

print 'Done'

print 'Splitting into tasks and converting to OSM XML...'
# Split into tasks, validate, and convert to OSM XML.
# for idx, task in tasks.iloc[[0]].iterrows():
for idx, task in tasks.iterrows():
    task_dirname = os.path.join(tasks_path, str(task['poly_id']))
    task_fname = 'University_District-{}.osm'.format(task['poly_id'])
    task_path = os.path.join(task_dirname, task_fname)

    if not os.path.exists(task_dirname):
        os.mkdir(task_dirname)

    task_layers = {}

    for key, value in layers_gdf.iteritems():
        # FIXME: need to remove redundant data (use poly_id!)
        # Extract
        data = value.loc[value.intersects(task.geometry)].copy()

        # Convert to GeoJSON
        the_json = osm.to_geojson(data)

        # Convert to osmizer intermediate format (OSM-compatible).
        features = osm.json_to_dom(the_json, featuretype=key)

        task_layers[key] = features

    # Combine OSM XML DOMs into a single DOM and dedupe
    # TODO: fix the way that merge works - it edits the first argument inplace.
    # same for dedupe...
    merged = task_layers['sidewalks']
    osm.merge(merged, task_layers['crossings'])
    osm.merge(merged, task_layers['curbramps'])
    osm.dedupe(merged)

    # Write to file
    osm.write_dom(merged, task_path)

print 'Done'
