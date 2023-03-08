# Docker file for wukong-robot
FROM wzpan/wukong-robot:v1.8.0
MAINTAINER wzpan
# Upgrade to python 3.8
RUN apt-get remove -y python3-pip
RUN apt-get autoremove -y
RUN apt-get install -y python3.8
RUN apt-get install -y python3-pip
RUN rm /usr/bin/python3
RUN ln -s /usr/bin/python3.8 /usr/bin/python3
RUN python3.8 -m pip install --upgrade pip
WORKDIR /root/wukong-robot
RUN git pull -f
RUN pip install -r requirements.txt
WORKDIR /root/.wukong/contrib
RUN git pull -f
RUN pip install -r requirements.txt
WORKDIR /root/wukong-robot
EXPOSE 5001
