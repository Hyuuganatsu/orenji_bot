FROM python:3.11

RUN apt-get update && apt-get install -y wget nano && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

WORKDIR /orenji_bot
COPY . /orenji_bot

#RUN pip3 install revChatGPT --upgrade

CMD ["python3","run.py"]