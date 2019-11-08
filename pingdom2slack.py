#!/usr/bin/env python

import datetime
import json
import os
import time

from flask import abort, Flask, jsonify, request
import requests

__version__ = "0.1.3"

app = Flask(__name__)

try:
    SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
    app.logger.debug("Slack webhook URL found in env variable")
except:
    SLACK_WEBHOOK = None
    app.logger.error("No Slack webhook URL found")
    abort(502)

try:
    PINGDOM_TOKEN = os.environ["PINGDOM_TOKEN"]
    app.logger.debug("Pingdom Token found in env variable")
except:
    PINGDOM_TOKEN = None
    app.logger.error("No Pingdom Token found")
    abort(502)


EMOJI_NUMBER = [
    ":one:",
    ":two:",
    ":three:",
    ":four:",
    ":five:",
    ":six:",
    ":seven:",
    ":eight:",
    ":nine:",
    ":keycap_ten:",
]


def pingdom_analysis(check_id, state_changed_timestamp):
    """Return pingdom analysis for a check.

    :param int check_id: Pingdom check id to search
    :param int state_changed_timestamp: RCA timestamp

    :return dict
    """
    headers = {"Authorization": "Bearer %s" % PINGDOM_TOKEN}

    url = "https://api.pingdom.com/api/3.1/analysis/%d" % check_id

    # Make the call
    response = requests.get(url, headers=headers)
    app.logger.debug(response.__dict__)
    if response.status_code != 200:
        app.logger.debug(response.content)
        return None

    analysis = response.json()["analysis"]
    analysis_ids = [
        test["id"]
        for test in analysis
        if test["timefirsttest"] == state_changed_timestamp
    ]
    if len(analysis_ids) == 0:
        app.logger.debug("No analysis id")
        return None
    else:
        app.logger.debug("pingdom analysis id = %d" % analysis_ids[0])

    url = "https://api.pingdom.com/api/3.1/analysis/%d/%d" % (check_id, analysis_ids[0])

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        app.logger.debug(response.content)
        return None
    else:
        return response.json()


def post_2_slack(channel, pingdom_data):
    """Post message to slack.

    :param str channel: Slack channel
    :param dict pingdom_data: Data received from webhook
    """

    start_time = time.time()

    status = pingdom_data["current_state"]

    icon_emoji = {"DOWN": ":warning:", "UP": ":ok:"}.get(status, ":ghost:")

    title_emoji = {
        "DOWN": os.environ.get("TITLE_EMOJI_DOWN", ":warning:"),
        "UP": os.environ.get("TITLE_EMOJI_UP", ":ok:"),
    }.get(status, ":ghost:")

    analysis = None
    if status == "DOWN":
        analysis = pingdom_analysis(
            pingdom_data["check_id"], pingdom_data["state_changed_timestamp"]
        )

    analysis_time = time.time()

    check_name = pingdom_data["check_name"]

    if "full_url" in pingdom_data["check_params"].keys():
        check_url = pingdom_data["check_params"]["full_url"]
    else:
        check_url = pingdom_data["check_params"]["hostname"]

    error = pingdom_data["long_description"]

    # Choose attachment colot
    color = {"DOWN": "danger", "UP": "good"}.get(status, "#0000FF")

    verify_certificate = {True: ":+1:", False: ":-1:"}.get(
        pingdom_data["check_params"]["verify_certificate"], ":thinking_face:"
    )
    basic_auth = {True: ":+1:", False: ":-1:"}.get(
        pingdom_data["check_params"]["basic_auth"], ":thinking_face:"
    )

    fields = []

    blocks = [
        {
            "text": {
                "text": "%s *%s* is *%s* %s"
                % (title_emoji, check_name, status, title_emoji),
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "text": {"text": "*Check URL*:\n%s" % (check_url), "type": "mrkdwn"},
            "type": "section",
        },
    ]

    BLOCK_ID_WEBHOOK_DATA = len(blocks)
    blocks.append(
        {
            "fields": [
                {
                    "text": "*Check Type:*\n%s" % pingdom_data["check_type"],
                    "type": "mrkdwn",
                },
                {
                    "text": "*Importance Level:*\n%s"
                    % pingdom_data["importance_level"],
                    "type": "mrkdwn",
                },
                {"text": "*Basic auth?:*\n%s" % basic_auth, "type": "mrkdwn"},
                {
                    "text": "*Verify Certificate:*\n%s" % verify_certificate,
                    "type": "mrkdwn",
                },
                {
                    "text": "*Response Time Threshold:*\n%s ms"
                    % pingdom_data["check_params"]["responsetime_threshold"],
                    "type": "mrkdwn",
                },
            ],
            "type": "section",
        }
    )

    if len(pingdom_data["tags"]) > 0:
        blocks[BLOCK_ID_WEBHOOK_DATA]["fields"].append(
            {
                "text": "*Tags:*\n%s"
                % ", ".join(["`%s`" % tag for tag in pingdom_data["tags"]]),
                "type": "mrkdwn",
            }
        )

    if len(pingdom_data.get("check_params", {}).get("shouldcontain", "")) > 0:
        blocks[BLOCK_ID_WEBHOOK_DATA]["fields"].append(
            {
                "text": "*Should Contain:*\n`%s`"
                % pingdom_data["check_params"]["shouldcontain"],
                "type": "mrkdwn",
            }
        )

    if len(pingdom_data.get("check_params", {}).get("shouldnotcontain", "")) > 0:
        blocks[BLOCK_ID_WEBHOOK_DATA]["fields"].append(
            {
                "text": "*Should Not Contain:*\n`%s`"
                % pingdom_data["check_params"]["shouldnotcontain"],
                "type": "mrkdwn",
            }
        )

    if len(pingdom_data.get("first_probe", {}).get("location", "")) > 0:
        blocks[BLOCK_ID_WEBHOOK_DATA]["fields"].append(
            {
                "text": "*First Probe:*\n%s" % pingdom_data["first_probe"]["location"],
                "type": "mrkdwn",
            }
        )

    if len(pingdom_data.get("second_probe", {}).get("location", "")) > 0:
        blocks[BLOCK_ID_WEBHOOK_DATA]["fields"].append(
            {
                "text": "*Second Probe:*\n%s"
                % pingdom_data["second_probe"]["location"],
                "type": "mrkdwn",
            }
        )

    if len(pingdom_data["custom_message"]) > 0:
        blocks.append(
            {
                "text": {
                    "text": "*Custom Message*: %s" % pingdom_data["custom_message"],
                    "type": "mrkdwn",
                },
                "type": "section",
            }
        )

    if status == "DOWN":
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "text": {
                    "text": "Downtime and *Root Cause Analysis* "
                    "(<https://www.pingdom.com/tutorial/downtime-root-cause/|read more>)",
                    "type": "mrkdwn",
                },
                "type": "section",
            }
        )

    analysis_counter = 0

    if analysis is None and status == "DOWN":
        blocks.append(
            {
                "text": {
                    "text": ":warning: Could no fetch analysis :warning: ",
                    "type": "mrkdwn",
                },
                "type": "section",
            }
        )
    elif analysis is not None:
        for task in analysis["analysisresult"]["tasks"]:

            blocks.append(
                {
                    "text": {
                        "text": "%s analysis" % EMOJI_NUMBER[analysis_counter],
                        "type": "mrkdwn",
                    },
                    "type": "section",
                }
            )
            fields = []
            raw_response = None

            for result in task["result"]:

                value = result["value"]

                if result["name"] == "timestamp":
                    value = datetime.datetime.fromtimestamp(
                        int(result["value"])
                    ).strftime("%Y-%m-%d %H:%M:%S")
                elif result["name"] == "raw_response":
                    # value = "```%s```" % "\n".join(result["value"])
                    raw_response = "\n".join(result["value"])
                    continue
                elif result["name"] == "communication_log":
                    continue
                    # if len(result["value"][0]["response_content"]) > 0:
                    #     value = "```%s```\n\n```%s```" % (
                    #         result["value"][0]["request"],
                    #         result["value"][0]["response_content"],
                    #     )
                    # else:
                    #     value = "```%s```" % (result["value"][0]["request"])

                fields.append(
                    {"text": "*%s:*\n%s" % (result["name"], value), "type": "mrkdwn"}
                )

            blocks.append({"fields": fields, "type": "section"})
            if raw_response is not None:
                blocks.append(
                    {
                        "text": {
                            "text": "*Raw Response:*\n```%s```" % raw_response,
                            "type": "mrkdwn",
                        },
                        "type": "section",
                    }
                )
            blocks.append({"type": "divider"})
            analysis_counter += 1

    # Let's build our payload
    payload = {
        "channel": channel,
        "blocks": blocks,
        "attachments": [],
        "icon_emoji": icon_emoji,
        "username": "Pingdom",
    }

    # Add specific headers
    headers = {"Content-Type": "application/json"}

    start_slack_notify = time.time()

    # Make the call
    response = requests.post(SLACK_WEBHOOK, headers=headers, data=json.dumps(payload))

    end_slack_notify = time.time()

    app.logger.debug(response.__dict__)
    if response.status_code == 200:
        return (
            jsonify(
                {
                    "analysis_time": analysis_time - start_time,
                    "process_time": start_slack_notify - analysis_time,
                    "notify_time": end_slack_notify - start_slack_notify,
                    "total_time": time.time() - start_time,
                }
            ),
            200,
        )
    else:
        app.logger.debug(response.content)
        return (
            jsonify(
                {
                    "analysis_time": analysis_time - start_time,
                    "process_time": start_slack_notify - analysis_time,
                    "notify_time": end_slack_notify - start_slack_notify,
                    "total_time": time.time() - start_time,
                    "content": response.content,
                }
            ),
            response.status_code,
        )


@app.route("/monitoring/health", methods=["GET"])
def health():
    status = 200
    if SLACK_WEBHOOK is None or PINGDOM_TOKEN is None:
        status = 500

    return (
        jsonify(
            {
                "SLACK_WEBHOOK": SLACK_WEBHOOK is not None,
                "PINGDOM_TOKEN": PINGDOM_TOKEN is not None,
                "version": __version__,
            }
        ),
        status,
    )


@app.route("/<channel>", methods=["POST"])
def slack_poster(channel):
    # Initialize the fields of our message
    check_name = None
    check_url = None
    status = None
    error = None

    app.logger.info("Post message to %s channel", channel)

    # Define a default channell
    if not channel:
        return jsonify({"error": "channel is missing"}), 400

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
