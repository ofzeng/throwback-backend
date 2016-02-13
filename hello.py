"""Cloud Foundry test"""
from flask import Flask, request
import os
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


@app.route("/request", methods = ["GET"])
def process_request():
    return requests.get('https://graph.facebook.com/me/photos/?fields=id,created_time&access_token=' + request.args['facebook_token']).content)
    # return data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
