# Docker file for wukong-robot
FROM wzpan/wukong-robot:v1.0.3
MAINTAINER wzpan
WORKDIR /root/wukong-robot
RUN git pull origin
RUN git checkout ycy
RUN git pull origin ycy # force
RUN pip3 install -r requirements.txt
RUN apt-get install emacs
WORKDIR /root/.wukong/contrib
RUN git pull
RUN wget http://hahack-1253537070.coscd.myqcloud.com/misc/photos.py
RUN pip3 install -r requirements.txt
WORKDIR /root/wukong-robot
EXPOSE 5000
