# This is a hacky file meant to represent our initail import - just the
# U district
import geopandas as gpd
import subtasks
import os
import shutil
import osm
import click


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
# TODO: iterate for all neighborhoods
neighborhood_name = 'University District'
neighborhood_escname = neighborhood_name.replace(' ', '_')
mask = neighborhoods['S_HOOD'] == neighborhood_name
udistrict = neighborhoods.loc[mask, 'geometry'].iloc[0]

tasks = subtasks.filter_blocks_by_poly(blocks, udistrict)

tasks.crs = crs
tasks = tasks.to_crs({'init': 'epsg:4326'})

# FIXME: create real URLs + real chunked data here
base_url = 'https://import.opensidewalks.com'
city = 'seattle'
folder = os.path.join(base_url, city, neighborhood_escname)
poly_ids = tasks['poly_id'].astype(str)
tasks['url'] = folder + '/' + poly_ids + '/' + neighborhood_escname + '-' + \
               poly_ids + '.osm'

# Prepare output directory
tasks_path = './output/{}'.format(neighborhood_escname)
if os.path.exists(tasks_path):
    shutil.rmtree(tasks_path)
os.mkdir(tasks_path)

udistrict_path = ('./output/{}/{}.geojson'.format(neighborhood_escname,
                                                  neighborhood_escname))
tasks.to_file(udistrict_path, driver='GeoJSON')

# Load source data, project, and split into tasks
layers = ['sidewalks', 'crossings', 'curbramps']
layers_gdf = {}

json_list = []
# Read the data into GeoDataFrames, store in dictionary
click.echo('Reading files...')
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

click.echo('Done')

click.echo('Splitting geometries into separate tasks...')
# Split into tasks, validate, and convert to OSM XML.
# for idx, task in tasks.iloc[[0]].iterrows():
seen_it = {
    'sidewalks': set(),
    'curbramps': set(),
    'crossings': set()
}

tasks_gdfs = {}

for idx, task in tasks.iterrows():
    click.echo('Processed task {} of {}'.format(idx, tasks.shape[0]))
    tasks_gdfs[idx] = {}

    for key, value in layers_gdf.iteritems():
        # FIXME: need to remove redundant data (use poly_id!)
        # Extract
        data = value.loc[value.intersects(task.geometry)].copy()

        # Check the set of IDs we've seen and remove the features if we've
        # already processed them into a task. Add the new IDs to the ID set for
        # this layer.
        data = data.loc[~data.index.isin(seen_it[key])]
        for layer_idx in list(data.index):
            seen_it[key].add(layer_idx)

        tasks_gdfs[idx][key] = data
click.echo('Done')


click.echo('Converting to OSM XML...')
# Convert to OSM XML
for idx, task in tasks.iterrows():
    task_dirname = os.path.join(tasks_path, str(task['poly_id']))
    task_fname = '{}-{}.osm'.format(neighborhood_escname, task['poly_id'])
    task_path = os.path.join(task_dirname, task_fname)

    if not os.path.exists(task_dirname):
        os.mkdir(task_dirname)

    task_layers = {}

    for key, value in layers_gdf.iteritems():
        data = tasks_gdfs[idx][key]

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

click.echo('Done')
