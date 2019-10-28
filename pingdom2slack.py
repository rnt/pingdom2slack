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
    SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
    app.logger.debug("Slack webhook URL found in env variable")
except:
    SLACK_WEBHOOK = False
    app.logger.error("No Slack webhook URL found")
    abort(502)


def post_2_slack(channel, pingdom_data):

    check_name = pingdom_data["check_name"]

    if "full_url" in pingdom_data["check_params"].keys():
        check_url = pingdom_data["check_params"]["full_url"]
    else:
        check_url = pingdom_data["check_params"]["hostname"]

    status = pingdom_data["current_state"]

    error = pingdom_data["long_description"]

    # Choose attachment colot
    color = {"DOWN": "danger", "UP": "good"}.get(status, "#0000FF")

    verify_certificate = {True: ":+1:", False: ":-1:"}.get(
        pingdom_data["check_params"]["verify_certificate"], ":thinking_face:"
    )

    fields = [
        {
            "short": True,
            "title": "Response Time Threshold",
            "value": "%d ms" % pingdom_data["check_params"]["responsetime_threshold"],
        },
        {"short": True, "title": "Verify Certificate", "value": verify_certificate},
    ]

    if len(pingdom_data["check_params"]["shouldcontain"]) > 0:
        fields.append(
            {
                "short": True,
                "title": "Should Contain",
                "value": "`%s`" % pingdom_data["check_params"]["shouldcontain"],
            }
        )

    if len(pingdom_data["check_params"]["shouldnotcontain"]) > 0:
        fields.append(
            {
                "short": True,
                "title": "Should Not Contain",
                "value": "`%s`" % pingdom_data["check_params"]["shouldnotcontain"],
            }
        )

    if len(pingdom_data["first_probe"]["location"]) > 0:
        fields.append(
            {
                "short": True,
                "title": "First Probe",
                "value": pingdom_data["first_probe"]["location"],
            }
        )

    if len(pingdom_data["second_probe"].get("location", "")) > 0:
        fields.append(
            {
                "short": True,
                "title": "Second Probe",
                "value": pingdom_data["second_probe"]["location"],
            }
        )

    # Let's build our payload
    payload = {
        "channel": channel,
        "blocks": [
            {
                "text": {
                    "text": "*%s* is *%s*." % (check_name, status),
                    "type": "mrkdwn",
                },
                "type": "section",
            },
            {
                "text": {
                    "text": "%s" % (pingdom_data["long_description"]),
                    "type": "mrkdwn",
                },
                "type": "section",
            },
            {
                "text": {"text": "URL: %s" % (check_url), "type": "mrkdwn"},
                "type": "section",
            },
            {
                "elements": [
                    {
                        "text": "State Changed: %s"
                        % pingdom_data["state_changed_utc_time"],
                        "type": "mrkdwn",
                    }
                ],
                "type": "context",
            },
        ],
        "attachments": [
            {
                "fallback": "%s is %s" % (check_name, status),
                "color": color,
                "mrkdwn_in": ["text"],
                "fields": fields,
            }
        ],
        "username": "Pingdom",
    }

    # Add specific headers
    headers = {"Content-Type": "application/json"}

    # Make the call
    r = requests.post(SLACK_WEBHOOK, headers=headers, data=json.dumps(payload))
    app.logger.debug(r.__dict__)
    if r.status_code == 200:
        return "OK", 200
    else:
        app.logger.debug(r.content)
        return "NOK", 400


@app.route("/monitoring/health", methods=["GET"])
def health():
    if SLACK_WEBHOOK:
        resp = make_response(json.dumps({"slack_webhook": True}), 200)
    else:
        resp = make_response(json.dumps({"slack_webhook": False}), 502)
    resp.headers["Content-Type"] = "application/json"
    return resp


@app.route("/<channel>", methods=["POST"])
def slack_poster(channel):
    # Initialize the fields of our message
    check_name = None
    check_url = None
    status = None
    error = None

    # Define a default channell
    if not channel:
        channel = "#devops"

    try:
        pingdom_data = request.get_json()
    except Exception as e:
        app.logger.error("Impossible to extract data from this pingdom call")
        app.logger.error(e)

    try:
        check_name = pingdom_data["check_name"]
    except Exception as e:
        app.logger.error("Impossible to extract check_name from this pingdom call")
        app.logger.error(e)
        app.logger.debug(pingdom_data)

    try:
        if "full_url" in pingdom_data["check_params"].keys():
            check_url = pingdom_data["check_params"]["full_url"]
        else:
            check_url = pingdom_data["check_params"]["hostname"]
    except Exception as e:
        app.logger.error("Impossible to extract the full_url from this pingdom call")
        app.logger.error(e)
        app.logger.debug(pingdom_data)

    try:
        status = pingdom_data["current_state"]
    except Exception as e:
        app.logger.error("Impossible to extract status from this pingdom call")
        app.logger.error(e)
        app.logger.debug(pingdom_data)

    try:
        error = pingdom_data["long_description"]
    except Exception as e:
        app.logger.error("Impossible to extract error message from this pingdom call")
        app.logger.error(e)
        app.logger.debug(pingdom_data)

    app.logger.debug(
        "Posting to %s: %s is %s"
        % (channel, pingdom_data["check_name"], pingdom_data["current_state"])
    )
    return post_2_slack("#%s" % channel, pingdom_data)


@app.route("/<channel>", methods=["GET"])
def slack_poster_get(channel):
    return "pingdom2slack : pingdom alerts to slack webhkook !"
