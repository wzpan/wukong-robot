# Docker file for wukong-robot
FROM wzpan/wukong-robot:v1.8.0
MAINTAINER wzpan
# Upgrade to python 3.9
RUN add-apt-repository -r ppa:jonathonf/python-3.6
RUN apt update
RUN apt install software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get remove -y python3-pip
RUN apt-get autoremove -y
RUN apt-get install -y python3.9
RUN apt-get install -y python3-pip
RUN rm /usr/bin/python3
RUN ln -s /usr/bin/python3.9 /usr/bin/python3
RUN python3.8 -m pip install --upgrade pip
WORKDIR /root/wukong-robot
RUN git pull -f
RUN pip install -r requirements.txt
WORKDIR /root/.wukong/contrib
RUN git pull -f
RUN pip install -r requirements.txt
WORKDIR /root/wukong-robot
EXPOSE 5001
