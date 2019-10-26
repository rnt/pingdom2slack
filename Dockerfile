FROM python:3.8.0-alpine3.10

ENV FLASK_APP=pingdom2slack.py
ENV FLASK_DEBUG=0

WORKDIR /app

COPY requirements.txt pingdom2slack.py ./

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]
