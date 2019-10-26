# pingdom2slack

Small app to hook pingdom app monitoring to slack.
The goal is to add the error message when one of your site is down.

## Usage

### With Docker

```
sudo docker run -d -e SLACK_WEBHOOK=https://xxxxxxxxxxxx -p 5000:5000 lotooo/pingdom2slack
```

### Standalone app

```
virtualenv -p python3.8 venv
source venv/bin/activate
pip install -r requirements.txt
export SLACK_WEBHOOK=https://xxxxxxxxxxxx
export FLASK_APP=pingdom2slack.py
flask run --host=0.0.0.0
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

docker run -e SLACK_WEBHOOK=https://xxxxxxxxxxxx -p 5000:5000 pingdom2slack:local
```


## Basic testing

[Pingdom webhooks](https://www.pingdom.com/resources/webhooks/) are available in official documentation.

And local testing example is:

```
curl -v -H "Content-Type: application/json" -d @payload/http.json localhost:5000/pingdom
```
