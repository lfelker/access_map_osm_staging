#About
This repo contains code to prepare sidewalk data for import into osm as an osm.xml file

Currently it requires the creation of a script to stage a particular area. See staging_judkins.py or staging_university_district.py for examples. The intent is to have a staging library (staging.py) that can be used for different types of data sources and staging areas to prepare sidewalk data for osm import.