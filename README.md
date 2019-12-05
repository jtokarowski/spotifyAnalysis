# Spotify Analysis

```
This program will retrieve user selected spotify playlists
and run clustering analysis on all contained songs.
The program will create 5 new playlists in the users
Spotify library according to their cluster assignment
based on the k-means algorithm in SKlearn. 
```

### Prerequisites

```
This program relies on the following python libraries:

json
flask
requests
urllib.parse
pymongo
pandas
numpy
flask_wtf
wtforms
sklearn 
```

## Getting Started
```
Sign up for a spotify developer account, and create a client ID at https://developer.spotify.com/dashboard/applications

Clone this repository, and create a file 'config.json' in the main application folder containing your spotify client id and secret developer key.

{
    "spotify":{
        "cid":"XYZ123",
        "secret":"XYZ123"
    }
}

Launch an instance of the mongo daemon, making sure to set the ulimit to 1028 if applicable. 

Change directory to the main folder and run python app.py.

Navigate to localhost:8000 in a browser to start the process.

Sign in to spotify and grant the application permission to read and write to public/private playlists.

Select playlists containing songs you want to analyze, hit the submit button at the bottom of the page.

You will be redirected to a new page with a visualization of the cluster center locations via a radar chart.
```

## Built With
```
* [Flask](http://flask.palletsprojects.com/en/1.1.x/) - The web framework used
```
## Authors
```
* **John Tokarowski** 
```
## Acknowledgments
```
https://github.com/drshrey/spotify-flask-auth-example
https://github.com/ahipolito94/Spotify-Analysis
```