"""Cloud Foundry test"""
from __future__ import print_function # In python 2.7
from flask import Flask, request, redirect
import sys
import os
import json
import codecs
import parser
import requests

app = Flask(__name__)

app.config['PROPAGATE_EXCEPTIONS'] = True

# On Bluemix, get the port number from the environment variable VCAP_APP_PORT
# When running this app on the local machine, default the port to 8080
port = int(os.getenv('VCAP_APP_PORT', 8080))

@app.route("/")
def hello():
    return request.args['facebook_token']

@app.route("/home", methods = ["GET", "POST"])
def home():
    return "Home Page"

@app.route("/getToken")
def getToken():
	return redirect("https://accounts.spotify.com/authorize/?client_id=b4f179be39ec4098b5b972cdad7f03fb&response_type=code&redirect_uri=https://throwback.mybluemix.net/getCode&scope=playlist-read-private%20user-library-read", code=302)

@app.route("/getCode")
def getCode():
	#return request.args['code']
	return requests.post("https://accounts.spotify.com/api/token", data = {"code": request.args['code'], "grant_type": "authorization_code", "redirect_uri": "https://throwback.mybluemix.net/getCode", "client_id": "b4f179be39ec4098b5b972cdad7f03fb", "client_secret": "c951d664306649d4a29f4411e1a9c56d"}).content

@app.route("/request", methods = ["GET"])
def process_request():
    r = requests.get('https://graph.facebook.com/me/photos/?fields=id,created_time&access_token=' + request.args['facebook_token'])
    photos = r.json()['data']

    r = requests.get('https://api.spotify.com/v1/me/tracks?access_token=' + request.args['spotify_token'])
    songs = r.json()['items']
    #photos = [{'id': 'p1', 'time': '2'}, {'id': 'p2', 'time': '3'},{'id': 'p3', 'time': '5'}]
    #songs =  [{'id': 's1', 'time': 1},{'id': 's2', 'time': 4}]
    matches = match_songs_photos(songs,photos)

    return jsonify(matches)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
