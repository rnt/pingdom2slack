FROM python:3.8.0-alpine3.10

WORKDIR /app

COPY requirements.txt pingdom2slack.py ./

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["gunicorn", "--bind=0.0.0.0:5000", "pingdom2slack:app"]
