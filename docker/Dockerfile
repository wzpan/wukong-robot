# Docker file for wukong-robot
FROM twylahelps/ubuntu-python36-swig:2
MAINTAINER wzpan
# use aliyun's mirror for faster download speed
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
# install all neccessary packages
RUN apt-get -y update
RUN apt-get install -y --fix-missing build-essential \
    wget git python-pyaudio python3-pyaudio sox ffmpeg && \
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
# update swig 3
WORKDIR /root
RUN wget http://hahack-1253537070.file.myqcloud.com/misc/swig-3.0.10.tar.gz
RUN tar xvf swig-3.0.10.tar.gz
WORKDIR /root/swig-3.0.10
RUN apt-get -y update
RUN apt-get install -y libpcre3 libpcre3-dev
RUN ./configure --prefix=/usr --without-clisp --without-maximum-compile-warnings
RUN make
RUN make install
RUN install -v -m755 -d /usr/share/doc/swig-3.0.10
RUN cp -v -R Doc/* /usr/share/doc/swig-3.0.10
RUN apt-get install -y libatlas-base-dev
# build _snowboydetect.so
WORKDIR /root
RUN wget http://hahack-1253537070.file.myqcloud.com/misc/snowboy.tar.bz2
RUN tar -xvjf snowboy.tar.bz2
WORKDIR snowboy/swig/Python3
RUN make
RUN cp _snowboydetect.so /root/wukong-robot/snowboy/
WORKDIR /root/wukong-robot
RUN git pull
RUN pip3 install -r requirements.txt
WORKDIR /root/.wukong/contrib
RUN git pull
RUN pip3 install -r requirements.txt
RUN apt-get install -y alsa-base pulseaudio libsox-fmt-all
WORKDIR /root/wukong-robot
EXPOSE 5000
