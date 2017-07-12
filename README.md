# pingdom2slack

Small app to hook pingdom app monitoring to slack
The goal is to add the error message when one of your site is down

## Usage

* With Docker :

```
sudo docker run -d -e SLACK_WEBHOOK=https://xxxxxxxxxxxx -p 5000:5000 lotooo/pingdom2slack
```

* Standalone app :
```
virtualenv -p python3.5 venv
source venv/bin/activate
pip install -r requirements.txt
export SLACK_WEBHOOK=https://xxxxxxxxxxxx
export FLASK_APP=pingdom2slack.py
flask run --host=0.0.0.0
```

## Debug

You can run the app with a specific env variables `FLASK_DEBUG=1` to enable debug logging.
