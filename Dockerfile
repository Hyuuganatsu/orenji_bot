FROM python:3.11

# install python deps
RUN apt-get update && apt-get install -y wget nano && \
    #apt-get upgrade -y python-pip &&\
    #apt-get install -y libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6 libxinerama-dev build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# install anaconda3
#ENV CONDA_DIR /opt/conda
#RUN wget https://repo.anaconda.com/archive/Anaconda3-2021.11-Linux-aarch64.sh && \
#    chmod +x Anaconda3-2021.11-Linux-aarch64.sh && \
#    bash Anaconda3-2021.11-Linux-aarch64.sh -b -p /opt/conda
#ENV PATH=$CONDA_DIR/bin:$PATH
#ENV OMP_NUM_THREADS=1

# install tensorflow-gpu and torch
#RUN conda install -y -c apple tensorflow-deps==2.8.0 && \
#    pip3 install -y tensorflow-macos==2.8.0 && \
#    pip3 install -y tensorflow-metal &&
#RUN conda install -y -c pytorch pytorch && \
#RUN pip3 install --upgrade pip && \
#RUN pip3 search graia-ariadne

WORKDIR /orenji_bot
COPY . /orenji_bot

RUN pip install -r requirements.txt

#RUN pip3 install revChatGPT --upgrade


CMD ["python3","run.py"]