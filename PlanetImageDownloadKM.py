# import libraries
import requests 
from requests.auth import HTTPBasicAuth
import os
import cgi
import pandas as pd
import time

# set API key
os.environ['PL_API_KEY'] = 'PLAKb5f3c747075e4c85835781aba011f7ab'
PLANET_API_KEY = os.getenv('PL_API_KEY')
#set working directory
wdir = r'C:\Users\kmeyers\OneDrive - Environmental Protection Agency (EPA)\Profile\Documents\PIP\Images'
os.chdir("C:/Users/kmeyers/OneDrive - Environmental Protection Agency (EPA)/Profile/Documents/PIP")
# read csv of image metadata 
df = pd.read_csv(os.path.join(wdir,'PlanetScope_Images.csv'))
# take a subset of the df, only want samples with PSB.SD as sensor, high AOI coverage, and low cloud percent
subset_df = df.loc[(df['sensor_id'] == 'PSB.SD') & (df['aoi_coverage'] > 99) & (df['cloud_percent'] == 0)]

#%%
#retrieve only image_ids for download and convert to a list
li = subset_df['image_id'].to_list()
li = li[0:5]  #comment out if needed, this reduces the list to first 5 images

#%%
#create a list of urls with specified requirements 
IDli = []
for i in li: 
    
    item_type = subset_df.loc[subset_df['image_id'] == i, 'item_type'].values.item()
    id_url = 'https://api.planet.com/data/v1/item-types/{}/items/{}/assets'.format(item_type, i)
    IDli.append(id_url)

#%%
for i in IDli:
    start = time.perf_counter()
    result = requests.get(i, auth=HTTPBasicAuth(PLANET_API_KEY, ''))
    #print(result.json().keys()) # List of asset types available for this particular satellite image
    selected_type = 'basic_analytic_8b' # specify the asset type you want. print the asset_types object to see what kind of asset types are available
    print(result.json()[selected_type]['status']) # This is "inactive" if the "analytic" asset has not yet been activated; otherwise 'active'
    ### Parse out useful links
    links = result.json()[selected_type]['_links']
    # Request activation of the asset:
    self_link = links['_self']
    activation_link = links['activate']
    activate_result = requests.get(activation_link, auth=HTTPBasicAuth(PLANET_API_KEY, ''))
    ### Check if asset has been 'activated', if not keep checking every 60 sec until the status has changed (this can take a few minutes). The time interval can be increased or decreased depending on your preferences
    activation_status = requests.get(self_link, auth=HTTPBasicAuth(PLANET_API_KEY, ''))
    activation_status_result = activation_status.json()['status']
    start_time = time.time()
    while activation_status_result != 'active':
      activation_status = requests.get(self_link, auth=HTTPBasicAuth(PLANET_API_KEY, ''))
      activation_status_result = activation_status.json()['status']
      time.sleep(60.0 - ((time.time() - start_time) % 60.0))
      print(activation_status_result)
    ### Image can be downloaded by making a GET with your Planet API key, from here:
    t2 = time.perf_counter()
    download_link = activation_status.json()['location'] # get the download link for the activated asset
    r = requests.get(download_link, stream = True) # request asset, store response
    if r.status_code == 200: # all systems are a go
      params = cgi.parse_header(r.headers['content-disposition'])[1] # parse asset parameters to extract filename 
      with open(os.path.join(wdir,params['filename']), 'wb') as f:
        for chunk in r.iter_content(1024): # this downloads the asset in 'chunks' which is often faster and less memory intensive for larger assets. It's currently set to 1024 bytes per chunk, but that can be changed
          out = f.write(chunk) # store default return value (bytes) in an object so it doesn't clutter your terminal
    finish = time.perf_counter()
    print('Finished activating' + f' in {round((t2-start)/60,2)} minutes.')
    print('finished downloading' + f'in{round((finish-t2)/60,2)} minutes.')
    print('Finished ' + str(i) + f' in {round((finish-start)/60,2)} minutes.')

