# Docker file for wukong-robot
FROM wzpan/wukong-robot:v1.8.0
MAINTAINER wzpan
WORKDIR /root/wukong-robot
RUN git pull -f
RUN pip install -r requirements.txt
WORKDIR /root/.wukong/contrib
RUN git pull -f
RUN pip install -r requirements.txt
WORKDIR /root/wukong-robot
EXPOSE 5000
