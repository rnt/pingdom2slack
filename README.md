# pingdom2slack

Small app to hook pingdom app monitoring to slack.
The goal is to add the error message when one of your site is down.

## Usage

The environment variables used are:

| Environment variable |                         Description                         |   Type   |   Default   |
|:--------------------:|:-----------------------------------------------------------:|:--------:|:-----------:|
|   `SLACK_WEBHOOK`    |                       Slack webhook.                        | Required |             |
|   `PINGDOM_TOKEN`    |                 Pingdom token for v3.1 API                  | Required |             |
|  `TITLE_EMOJI_DOWN`  | Emoji to use in the title, when the notification is by DOWN | Optional | `:warning:` |
|   `TITLE_EMOJI_UP`   |  Emoji to use in the title, when the notification is by UP  | Optional |   `:ok:`    |


### With Docker

```
sudo docker run -d -e SLACK_WEBHOOK=https://***** -e PINGDOM_TOKEN=***** -p 5000:5000 rnt/pingdom2slack
```

### Standalone app

```
virtualenv -p python3.8 venv
source venv/bin/activate
pip install -r requirements.txt
export SLACK_WEBHOOK=https://*****
export PINGDOM_TOKEN=*****
```

#### Development server

```
export FLASK_APP=pingdom2slack.py
flask run --host=0.0.0.0
```

#### Production server

```
gunicorn --bind=0.0.0.0:5000 pingdom2slack:app
```

## Debug

You can run the app with a specific env variables `FLASK_DEBUG=1` to enable debug logging.


## Compile requirements

```
pip install pip-tools
pip-compile --output-file requirements.txt requirements.in
```

## Build & Run

```
docker build -t pingdom2slack:local .

docker run -e SLACK_WEBHOOK=https://***** -e PINGDOM_TOKEN=***** -p 5000:5000 pingdom2slack:local
```


## Basic testing

[Pingdom webhooks](https://www.pingdom.com/resources/webhooks/) are available in official documentation.

And local testing example is:

```
curl -v -H "Content-Type: application/json" -d @payload/http.json localhost:5000/test_channel
```
