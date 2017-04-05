# This is a hacky file meant to represent our initail import - just the
# U district
import geopandas as gpd
import subtasks
import os
import shutil
import osm
import click
import staging


crs = {'init': 'epsg:26910'}
# Get the streets shapefile
streets = gpd.read_file('./inputdata/streets.shp').to_crs(crs)

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

layers = ['sidewalks', 'crossings', 'curbramps']
layers_gdf = {}

# Read the data into GeoDataFrames, store in dictionary
click.echo('Reading files...')
for layer in layers:
    gdf = gpd.read_file(os.path.join('./inputdata/', layer + '.shp'))

    # Reproject
    gdf = gdf.to_crs({'init': 'epsg:4326'})
    layers_gdf[layer] = gdf 

staging.stage(streets, udistrict, "University District", layers_gdf)


