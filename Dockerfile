FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1

RUN mkdir /src
WORKDIR /src
COPY requirements.txt /src/
RUN pip install -r requirements.txt
RUN pip install docker
COPY . /src/

CMD [ "python", "./bot.py" ]

#docker build -t botmaster .
#docker run -d --name ibrat-masterclass-container botmaster