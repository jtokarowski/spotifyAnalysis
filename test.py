import sys
import spotipy
import spotipy.util as util
import json

scope = 'user-library-read'

#retrieves the credentials from config.json
with open('config.json') as json_data_file:
    configData = json.load(json_data_file)

cid = configData["spotify"]["cid"]
secret = configData["spotify"]["secret"]
username = configData["spotify"]["username"]

token = util.prompt_for_user_token(username,scope,client_id=cid,client_secret=secret,redirect_uri='http://localhost/')


if token:
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    for item in results['items']:
        track = item['track']
        print(track['name'] + ' - ' + track['artists'][0]['name'])
else:
    print("Can't get token for", username)