FROM python:3.11

RUN apt-get update && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y wget nano libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 inotify-tools ffmpeg ./google-chrome-stable_current_amd64.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /orenji_bot
#COPY . /orenji_bot

#RUN pip3 install revChatGPT --upgrade

# run inotifywait to watch for code change in background. Then start the app in foreground.
# if file changes, inotifywait kills the app, and docker's restart: always will restart the app with code change.
CMD ["sh", "-c", "inotifywait -r -m -e modify,create,delete,move --exclude '__pycache__' /orenji_bot/modules | while read path action file; do echo \"$file changed, restarting run.py\"; pkill -f /orenji_bot/run.py; python3 -u /orenji_bot/run.py & done & python3 -u /orenji_bot/run.py"]
