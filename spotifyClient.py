from __future__ import print_function
import sys
import requests
import json
import time

#URLS
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

class Spotify:
  def __init__(self, access_token):
    self.access_token = access_token

  def profile(self):
  	user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
  	authorization_header = {"Authorization": "Bearer {}".format(self.access_token)}
  	profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
  	profile_data = json.loads(profile_response.text)
  	userName = profile_data["display_name"]
  	return userName