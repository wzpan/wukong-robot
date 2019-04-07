# Docker file for wukong-robot
FROM wzpan/wukong-robot:v1.0.3
MAINTAINER wzpan
WORKDIR /root/wukong-robot
RUN git pull
RUN pip3 install -r requirements.txt
WORKDIR /root/.wukong/contrib
RUN git pull
RUN pip3 install -r requirements.txt
WORKDIR /root/wukong-robot
EXPOSE 5000
