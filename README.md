# Spotify Analysis

This program will retrieve user selected spotify playlists and run clustering analysis on all contained songs. The program will create 5 new playlists in the users spotify library according to their cluster assignment.

## Getting Started

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


### Prerequisites

This program relies on the following python libraries:


```
json
flask
requests
urllib.parse
pymongo
pandas
numpy
matplotlib.pyplot
flask_wtf
wtforms
seaborn
sklearn 
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```


## Built With

* [Flask](http://flask.palletsprojects.com/en/1.1.x/) - The web framework used

## Authors

* **John Tokarowski** 

## Acknowledgments

https://github.com/drshrey/spotify-flask-auth-example
https://github.com/ahipolito94/Spotify-Analysis

README

Simple web app to get user spotify playlist data and run analysis on it

Goal functionality- scrape DJ sets from mixesdb.com, make playlist, examine set structure

Current version
Step0: User logs into spotify, application gets Auth Token
Step1: Application uses token to retireve all user playlists
Step2: Application retrieves all song URI's in all playlists
Step3: Application Retrieves all song attributes for all URI's
Step4: Analysis- Logistic Regression, Kmeans, Etc.

Code adapted from several Github repositories including:

https://github.com/drshrey/spotify-flask-auth-example

