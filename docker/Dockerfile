# Docker file for Hexo 2
FROM ubuntu:16.04
MAINTAINER wzpan
# use aliyun's mirror for faster download speed
# RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
# install all neccessary packages
RUN apt-get update
RUN apt-get install -y --fix-missing build-essential \
    wget git python-pyaudio python3-pyaudio sox && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /root/
# install pip3
RUN wget https://bootstrap.pypa.io/get-pip.py --no-check-certificate
RUN python3 get-pip.py
# clone main repo
RUN git clone https://github.com/wzpan/wukong-robot.git
# clone .wukong repo
RUN mkdir /root/.wukong
WORKDIR /root/.wukong
RUN git clone https://github.com/wzpan/wukong-contrib.git contrib
WORKDIR /root/wukong-robot/snowboy/
RUN wget http://hahack-1253537070.file.myqcloud.com/misc/snowboy-ubuntu16.04/_snowboydetect.so
WORKDIR /root/wukong-robot
RUN apt-get install python-all-dev python3-all-dev
RUN git pull
RUN pip3 install -r requirements.txt
WORKDIR /root/.wukong/contrib
RUN git pull
RUN pip3 install -r requirements.txt
WORKDIR /root/wukong-robot
EXPOSE 5000