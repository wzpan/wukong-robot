# wukong-robot

> 注意：本项目目前还在开发阶段。

wukong-robot 是一个简单灵活的中文语音对话机器人。

## 系统要求 ##

wukong-robot 支持运行在以下的设备和系统中：

* 64bit Mac OS X
* 64bit Ubuntu（12.04 and 14.04）
* 全系列的树莓派（Raspbian 系统）
* Pine 64 with Debian Jessie 8.5（3.10.102）
* Intel Edison with Ubilinux （Debian Wheezy 7.8）

## 安装 ##

1. 克隆本仓库：

``` bash
git clone https://github.com/wzpan/wukong-robot.git
```

2. 安装 sox ：

* Linux 系统：

``` bash
sudo apt-get install python-pyaudio python3-pyaudio sox
```

* Mac 系统：

``` bash
brew install portaudio sox
```

> 如果你没有 Homebrew ，参考[本文](http://brew.sh/)安装

3. 安装依赖的库：

``` bash
cd wukong-robot
pip install -r requirements.txt
```

4. 获取 _snowboydetect.so

snowboy 为不同平台提供了 so 包，[到官网下载你的平台适用的版本](http://docs.kitt.ai/snowboy/)，解压后将 _snowboydetect.so 拷贝到 snowboy 目录中。

你也可以 [手动编译](https://github.com/wzpan/snowboy) ，以支持更多的平台。

## 运行 ##

``` bash
python wukong.py
```

第一次启动时将提示你是否要到用户目录下创建一个配置文件，输入 `y` 即可。

## 配置 ##

参考[配置文件的注释](https://github.com/wzpan/wukong-robot/blob/master/static/default.yml)进行配置即可。注意不建议直接修改 default.yml 里的内容，否则会给后续通过 `git pull` 更新带来麻烦。你应该拷贝一份放到 `$HOME/.wukong/config.yml` 中，或者在运行的时候按照提示让 wukong 为你完成这件事。

几个 tips：

1. 建议在运行 wukong-robot 的机器上重新训练一下唤醒词，不同设备录制出来的唤醒词模型使用效果会大打折扣。
2. 不论使用哪个厂商的API，都建议注册并填上自己注册的应用信息，而不要用默认的配置。这是因为这些API都有使用频率和并发数限制，过多人同时使用会影响服务质量。
