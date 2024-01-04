######################################################################## summary
#This script allows the user to search for Planet Labs imagery using their API
#The script creates a list of filters with different time chunks and loops through these to keep # of files below 250 page limit
#This loop identifies PlanetScope images that provide coverage of the polygons and satisfy additional criteria like cloud cover and date range
# While AOI (polygon) coverage can't be used as a filter other filters can be added and the current filters can be removed depending on your needs
# AOI coverage is computed and stored for each image along with other pertinent metadata parameters like image id, strip id, sensor id, date, time, and cloud cover. Other parameters can be stored depending on your needs
# Results of the search are saved as "PlanetScope_images.csv"
######################################################################## import python packages
import os
import json
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from shapely.geometry import Polygon
import numpy as np
import re

# set working directory 
os.chdir("C:/Users/kmeyers/OneDrive - Environmental Protection Agency (EPA)/Profile/Documents/PIP")
# Helper function to printformatted JSON using the json module
def p(data):
    print(json.dumps(data, indent=2))
# set API key
os.environ['PL_API_KEY'] = 'PLAKb5f3c747075e4c85835781aba011f7ab'
API_KEY = os.getenv('PL_API_KEY')
# construct auth tuple for use in the requests library
BASIC_AUTH = (API_KEY, '')

# Setup Planet Data API base URL
URL = "https://api.planet.com/data/v1"
session = requests.Session() # Setup the session
session.auth = (API_KEY, "") # Authenticate
res = session.get(URL) # Make a GET request to the Planet Data API
res.status_code # Response status code
res.text # Response Body
stats_url = "{}/stats".format(URL) # Setup the stats URL
#%%
# William O. Huske Dam & Lock and Dam 1 bounding boxes 
# Ensure first and last coordinates are the same
# If more locations are added a df can be created storing the locations and added into the 
# filters loop. For now manually change between the two locations

WOH = [[-78.824336,34.836093], [-78.823602,34.831476], [-78.820856,34.831675],[-78.822047,34.836194], [-78.824336,34.836093]]
LD1 = [[-78.295305,34.405783], [-78.292539,34.401953], [-78.29066,34.403035],[-78.293381,34.406617], [-78.295305,34.405783]]

geom = {
  "type": "Polygon",
  "coordinates": [ WOH ]  }

#create a polygon object out of AOI geometry
aoi_coords = np.array(WOH)
aoi = Polygon(aoi_coords)
#%%
#This gives you a quick check of how many images you can expect over a time period with given filters
#Create 3 filters cloud cover, date, and geometry
#You can get statistics from all available data but be aware that there is a 30 day embargo on downloading images
    #lte: less than or equal, gte: greater than or equal

# Specify the sensors/satellites or "item types" to include in our results
item_types = ["PSScene"]

#get all images within a date range
date_filter = { 
    "type": "DateRangeFilter", # Type of filter -> Date Range
    "field_name": "acquired", # The field to filter on: "acquired" -> Date on which the "image was taken"
    "config": {
        "gte": "2015-01-01T00:00:00.000Z", 
        "lte": "2024-12-31T00:00:00.000Z",
}}
# get images that overlap with our AOI 
geometry_filter = {
  "type": "GeometryFilter",
  "field_name": "geometry",
  "config": geom
}
#only get images with lte a certain % cloud coverage 
cloud_cover_filter = {
  "type": "RangeFilter",
  "field_name": "cloud_cover",
  "config": {
    "lte": 0.3
}}
# combine our geo, date, cloud filters
combined_filter = {
  "type": "AndFilter",
  "config": [geometry_filter, date_filter, cloud_cover_filter]
}

# Construct the request.
request = {
    "item_types" : item_types,
    "interval" : "year", #this can be changed to hour, day, week, month or year
    "filter" : combined_filter
  }

# Send the POST request to the API stats endpoint
res=session.post(stats_url, json=request)
# Print response
p(res.json())

#%% 

#Create 1/2 year time chunks to loop through so data downloaded will be less than 250 rows (page limit)
#There is a way to just flip through pages (see Peters code "ImageSearch) 
#I couldn't get that to work so this is my inelegant way around that

chunk_start = ["2015-01-01T00:00:00.000Z", "2015-06-01T00:00:00.000Z", 
               "2016-01-01T00:00:00.000Z", "2016-06-01T00:00:00.000Z", 
               "2017-01-01T00:00:00.000Z", "2017-06-01T00:00:00.000Z", 
               "2018-01-01T00:00:00.000Z", "2018-06-01T00:00:00.000Z", 
               "2019-01-01T00:00:00.000Z", "2019-06-01T00:00:00.000Z", 
               "2020-01-01T00:00:00.000Z", "2020-06-01T00:00:00.000Z", 
               "2021-01-01T00:00:00.000Z", "2021-06-01T00:00:00.000Z", 
               "2022-01-01T00:00:00.000Z", "2022-06-01T00:00:00.000Z", 
               "2023-01-01T00:00:00.000Z", "2023-06-01T00:00:00.000Z", 
               ]

chunk_end = ["2015-06-01T00:00:00.000Z", "2016-01-01T00:00:00.000Z",
             "2016-06-01T00:00:00.000Z", "2017-01-01T00:00:00.000Z",
             "2017-06-01T00:00:00.000Z", "2018-01-01T00:00:00.000Z",
             "2018-06-01T00:00:00.000Z", "2019-01-01T00:00:00.000Z",
             "2019-06-01T00:00:00.000Z", "2020-01-01T00:00:00.000Z",
             "2020-06-01T00:00:00.000Z", "2021-01-01T00:00:00.000Z",
             "2021-06-01T00:00:00.000Z", "2022-01-01T00:00:00.000Z",
             "2022-06-01T00:00:00.000Z", "2023-01-01T00:00:00.000Z",
             "2023-06-01T00:00:00.000Z", "2024-01-01T00:00:00.000Z",
              ]
#%%
#create a list of filters with dates split into 1/2 year chunks
#This is dependent on previous geometry and cloud cover filter, will ignore past date filter

li=[]
for x,y in zip(chunk_start, chunk_end):
    date_filter = {
        "type": "DateRangeFilter", # Type of filter -> Date Range
        "field_name": "acquired", # The field to filter on: "acquired" -> Date on which the "image was taken"
        "config": {
            "gte": x, # "gte" -> Greater than or equal to
            "lte": y,
        }
    }
    
    # combine our geo, date, cloud filters
    combined_filter = {
      "type": "AndFilter",
      "config": [geometry_filter, date_filter, cloud_cover_filter]
    }
    
    li.append(combined_filter)
#%%
#Find all images and relevant meta data by looping through time chunks
item_type = "PSScene"
results=[]
#loop through list of filters and find properties 
for item in li:   
    # API request object
    search_request = {
      "item_types": [item_type], 
      "filter": item
    }

    # fire off the POST request
    search_result = \
      requests.post(
        'https://api.planet.com/data/v1/quick-search',
        auth=HTTPBasicAuth(API_KEY, ''),
        json=search_request)

    geojson = search_result.json()
    image_list = pd.DataFrame(columns = ['image_id', 'strip_id', 'sensor_id', 'date', 'time', 'cloud_percent', 'item_type', 'image_geom']) # dataframe to store pertinent metadata parameters 
    image_list['image_id'] = [feature.get('id', 'NA') for feature in geojson['features']] # image id
    image_list['strip_id'] = [feature['properties'].get('strip_id', 'NA') for feature in geojson['features']] # strip id
    image_list['sensor_id'] = [feature['properties'].get('instrument', 'NA') for feature in geojson['features']] # semnsor type
    acquisition = [re.split('T|\.|Z', a) for a in [feature['properties'].get('acquired', 'NA') for feature in geojson['features']]] # aquisition date and time
    image_list['date'] = [item[0] for item in acquisition] # date
    image_list['time'] = [item[1] for item in acquisition] # time
    image_list['cloud_percent'] = [feature['properties'].get('cloud_percent', 'NA') for feature in geojson['features']] # percent of the image impacted by clouds 
    image_list['image_geom'] = [feature['geometry'].get('coordinates', 'NA') for feature in geojson['features']] #Image coordinates
    image_list['item_type'] = item_type # add Planet Labs image type for downloading purposes in the future
    results.append(image_list)
output = pd.concat(results)
      
#%%
#a series of definitions to convert image coordinates to AOI % overlap. This is faster than including it in loop
#create and apply definition to extract coordinate list from its current formatting
def get_coord(li):
    coords = [item for sublist in li for item in sublist]
    return coords

output['image_coords'] = output['image_geom'].apply(lambda x: get_coord(x))

#create and apply definition to convert coordinate lists to a polygon
def get_poly(li):
    poly = Polygon(li)
    return poly

output['image_area'] = output['image_coords'].apply(lambda x: get_poly(x))    

#create and apply definition that finds the area overlap between image and aoi, and then divides by the aoi and *100 to get % overlap
def get_aoi(li):
    aoi_coverage =  ((li.intersection(aoi).area)/(aoi.area))*100
    return aoi_coverage

output['aoi_coverage'] = output['image_area'].apply(lambda x:get_aoi(x))

#%%
output.to_csv('PlanetScope_images.csv', index = True) 
