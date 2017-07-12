#!/usr/bin/env python

from flask import Flask
from flask import request
from flask import abort
from flask import make_response
import requests
import json
import os

app = Flask(__name__)

try:
    SLACK_WEBHOOK=os.environ['SLACK_WEBHOOK']
    app.logger.debug("Slack webhook URL found in env variable")
except:
    SLACK_WEBHOOK=False
    app.logger.error("No Slack webhook URL found")
    abort(502)

def post_2_slack(channel, check_name, check_url, status, error):
    # Choose attachment colot
    if status == "UP":
        color="good"
    else:
        color="danger"

    # Let's build our payload
    payload = {
        "channel" : channel,
        "attachments" : [{
           "fallback"  	: "%s is %s" % (check_name, status),
	   "color" 	: color,
           "mrkdwn_in"  : ["text"],
           "title"      : "%s is %s" % (check_name, status)
        }]
    }

    if status == "DOWN":
        payload['attachments'][0]['text'] = "%s | %s" % (check_url, error)

    # Add specific headers
    headers = { "Content-Type": "application/json"}

    # Make the call
    r = requests.post(SLACK_WEBHOOK, headers=headers, data=json.dumps(payload))
    if r.status_code == 200:
        return "OK", 200
    else:
        app.logger.debug(r.content)
        return "NOK", 400

@app.route("/monitoring/health", methods=['GET'])
def health():
    if SLACK_WEBHOOK:
    	resp = make_response(json.dumps({ "slack_webhook" : True }), 200)
    else:
    	resp = make_response(json.dumps({ "slack_webhook" : False }), 502) 
    resp.headers['Content-Type'] = "application/json"
    return resp

@app.route("/<channel>", methods=['GET', 'POST'])
def slack_poster(channel):
    if request.method == 'POST':
        # Initialize the fields of our message
        check_name 	= None
        check_url 	= None
        status 		= None
        error 		= None

        # Define a default channell
        if not channel:
            channel = "#devops"

        try:
            pingdom_data = request.get_json()
        except Exception as e:
            app.logger.error("Impossible to extract data from this pingdom call")
            app.logger.error(e)

        try:
            check_name = pingdom_data['check_name']
        except Exception as e:
            app.logger.error("Impossible to extract check_name from this pingdom call")
            app.logger.error(e)
            app.logger.debug(pingdom_data)

        try:
            if 'full_url' in pingdom_data['check_params'].keys():
                check_url = pingdom_data['check_params']['full_url']
            else:
                check_url = pingdom_data['check_params']['hostname']
        except Exception as e:
            app.logger.error("Impossible to extract the full_url from this pingdom call")
            app.logger.error(e)
            app.logger.debug(pingdom_data)
        
        try:
            status = pingdom_data['current_state']
        except Exception as e:
            app.logger.error("Impossible to extract status from this pingdom call")
            app.logger.error(e)
            app.logger.debug(pingdom_data)

        try:
            error = pingdom_data['long_description']
        except Exception as e:
            app.logger.error("Impossible to extract error message from this pingdom call")
            app.logger.error(e)
            app.logger.debug(pingdom_data)

        app.logger.debug("Posting to %s: %s is %s" % (channel, check_name, status))
        return post_2_slack("#%s" % channel,check_name, check_url, status, error)
    else:
        return "pingdom2slack : pingdom alerts to slack webhkook !"
