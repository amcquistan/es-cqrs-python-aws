FROM python:3.8-slim

RUN apt-get update && apt-get install curl -y

WORKDIR /opt/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ./startup.sh
