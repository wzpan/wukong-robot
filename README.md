# wukong-robot

<p align="center">
  <a href="https://wukong.hahack.com" target="_blank">
    <img width="128" src="http://hahack-1253537070.file.myqcloud.com/images/wukong-icons/256_256.png" alt="wukong-robot">
  </a>
</p>

<p align="center">
  wukong-robot 是一个简单、灵活、优雅的中文语音对话机器人/智能音箱项目，目的是让中国的 Maker 和 Haker 们也能快速打造个性化的智能音箱。wukong-robot 还可能是第一个开源的脑机唤醒智能音箱。
</p>

<p align="center">
  <a href="https://github.com/users/wzpan/projects/1"><img alt="wukong-project" src="https://img.shields.io/badge/project-wukong-informational.svg?style=flat-square"></a>
  <a href="https://wukong.hahack.com/#/donate"><img alt="捐赠" src="https://img.shields.io/badge/%EF%BF%A5-donate-green.svg?style=flat-square"></a>
  <a href="https://travis-ci.org/wzpan/wukong-robot"><img alt="Travis" src="https://img.shields.io/travis/wzpan/wukong-robot.svg?style=flat-square"></a>
  <a href="#"><img alt="Python3" src="https://img.shields.io/badge/Python-3-blue.svg?style=flat-square"></a>
  <a href="https://hub.docker.com/r/wzpan/wukong-robot"><img alt="docker-pulls" src="https://img.shields.io/docker/pulls/wzpan/wukong-robot.svg?style=flat-square&colorB=success"></a>
  <a href="https://github1s.com/wzpan/wukong-robot"><img alt="browse-code" src="https://img.shields.io/badge/browse-code-purple.svg?style=flat-square"></a>
</p>

<p align="center">
  <a href="https://opencollective.com/wukong-robot/contribute/tier/8131-sponsor" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsors.svg?avatarHeight=36"></a>
</p>

## Table of Contents

* [特性](#特性)
* [Demo](#demo)
* [环境要求](#环境要求)
* [安装](#安装)
* [升级](#升级)
* [运行](#运行)
* [配置](#配置)
* [技能插件](#插件)
* [API接口](#api-接口)
* [捐赠](#捐赠)
* [贡献](#贡献)
* [联系](#联系)
* [感谢](#感谢)
* [FAQ](#faq)
* [免责声明](#免责声明)

## 特性

<p align="center">
  <img src="https://hahack-1253537070.file.myqcloud.com/images/wukong-docs/wukong-robot-mindmap.png?version=20191123" alt="wukong-robot">
</p>

* 模块化。功能插件、语音识别、语音合成、对话机器人都做到了高度模块化，第三方插件单独维护，方便继承和开发自己的插件。
* 中文支持。集成百度、科大讯飞、阿里、腾讯等多家中文语音识别和语音合成技术，且可以继续扩展。
* 对话机器人支持。支持基于 AnyQ 的本地对话机器人，并支持接入图灵机器人、Emotibot 等在线对话机器人。
* 全局监听，离线唤醒。支持 Muse 脑机唤醒，及无接触的离线语音指令唤醒。
* 灵活可配置。支持定制机器人名字，支持选择语音识别和合成的插件。
* 智能家居。支持和 mqtt、HomeAssistant 等智能家居协议联动，支持语音控制智能家电。
* 后台配套支持。提供配套后台，可实现远程操控、修改配置和日志查看等功能。
* 开放API。可利用后端开放的API，实现更丰富的功能。
* 安装简单，支持更多平台。相比 dingdang-robot ，舍弃了 PocketSphinx 的离线唤醒方案，安装变得更加简单，代码量更少，更易于维护并且能在 Mac 以及更多 Linux 系统中运行。

wukong-robot 的工作模式：

<p align="center">
  <img src="http://hahack-1253537070.file.myqcloud.com/images/wukong-docs/wukong-robot-workflow.png" alt="wukong-robot 的工作模式">
</p>

wukong-robot 被唤醒后，用户的语音指令先经过 ASR 引擎进行 ASR 识别成文本，然后对识别到的文本进行 NLU 解析，再将解析结果进行技能匹配，交给适合处理该指令的技能插件去处理。插件处理完成后，得到的结果再交给 TTS 引擎合成成语音，播放给用户。

虽然一次交互可能包含多次网络请求，不过带来的好处是：每一个环节都可以被修改和定制。而且我认为，到了 5G 时代，音箱的响应速度将不再成为体验问题。可定制和个性化才是未来的主流，而届时 wukong-robot 将会是更好的选择！

## Demo

<p align="center">
  <img src="http://hahack-1253537070.file.myqcloud.com/images/wukong-docs/user-demo.jpg" alt="demo">
</p>

* Demo视频：
  - [ycy-robot 月芽特别定制版](https://www.bilibili.com/video/av50685517/)
  - [使用脑机唤醒 wukong-robot](https://www.bilibili.com/video/av76739580/)
  - [Google AIY Voice Kit + wukong-robot](https://www.bilibili.com/video/av81173082/)
* 后台管理端 Demo
  - 体验地址：https://bot.hahack.com  （体验用户名：wukong；体验密码：wukong@2019）

## 环境要求 ##

### Python 版本 ###

wukong-robot 只支持 Python 3.5+，不支持 Python 2.x 。

### 设备要求 ###

wukong-robot 支持运行在以下的设备和系统中：

* 64bit Mac OS X
* 64bit Ubuntu（12.04 and 14.04）
* 全系列的树莓派（Raspbian 系统）
* Pine 64 with Debian Jessie 8.5（3.10.102）
* Intel Edison with Ubilinux （Debian Wheezy 7.8）
* 装有 WSL（Windows Subsystem for Linux） 的 Windows

## 安装 ##

见 [wukong-robot 安装教程](https://wukong.hahack.com/#/install) 。

## 升级

``` bash
python3 wukong.py update
```

如果提示升级失败，可以尝试在 wukong-robot 的根目录手动执行以下命令，看看问题出在哪。

``` sh
git pull
pip3 install -r requirements.txt
```

## 运行 ##

``` bash
python3 wukong.py
```

建议在 [tmux](http://blog.jobbole.com/87278/) 或 supervisor 中执行。

第一次启动时将提示你是否要到用户目录下创建一个配置文件，输入 `y` 即可。

然后通过唤醒词 “孙悟空” 唤醒 wukong-robot 进行交互（该唤醒词可自定义）。

要让 wukong-robot 暂时屏蔽离线监听，可以在配置文件中设置 `hotword_switch` 为 true：

``` yaml
# 勿扰模式，该时间段内自动进入睡眠，避免监听
do_not_bother:
    ...
    hotword_switch: false  # 是否使用唤醒词开关唤醒模式
    ...
```

然后使用热词 “悟空别吵”；要让 wukong-robot 恢复离线监听，可以使用热词 “悟空醒醒”。

此外，wukong-robot 默认在运行期间还会启动一个后台管理端，提供了远程对话、查看修改配置、查看 log 等能力。

- 默认地址：http://localhost:5000
- 默认账户名：wukong
- 默认密码：wukong@2019

建议正式使用时修改用户名和密码，以免泄漏隐私。

## 配置 ##

参考[配置文件的注释](https://github.com/wzpan/wukong-robot/blob/master/static/default.yml)进行配置即可。注意不建议直接修改 default.yml 里的内容，否则会给后续通过 `git pull` 更新带来麻烦。你应该拷贝一份放到 `$HOME/.wukong/config.yml` 中，或者在运行的时候按照提示让 wukong-robot 为你完成这件事。

几个 tips：

1. 建议在运行 wukong-robot 的机器上重新训练一下唤醒词，不同设备录制出来的唤醒词模型使用效果会大打折扣。
2. 不论使用哪个厂商的API，都建议注册并填上自己注册的应用信息，而不要用默认的配置。这是因为这些API都有使用频率和并发数限制，过多人同时使用会影响服务质量。

## 技能插件 ##

* [官方插件列表](https://wukong.hahack.com/#/official)
* [用户贡献插件](https://wukong.hahack.com/#/contrib)

## API 接口 ##

wukong-robot 的后台接口是开放 Web API 的，可以使用 Restful 方式调用，见 [后台API](https://wukong.hahack.com/#/api)。

## 捐赠

您的捐赠将鼓励我继续完善 wukong-robot。

* 对于个人用户，可以使用支付宝或者微信进行捐赠，单笔超过 100 元的捐赠者，您的 ID 将可以出现在 wukong-robot 后台管理端的捐赠页面中。

 
| 支付宝 | 微信支付 |
| ------ | --------- |
| <img src="http://hahack.com/images/misc/alipay.png" height="248px" width="164px" title="支付宝" style="display:inherit;"/> | <img src="http://hahack.com/images/misc/wechatpay.jpeg" height="248px" width="164px" title="微信支付" style="display:inherit;"/> |

如果以上的图裂了，可以下载图片（[支付宝](http://hahack.com/images/misc/alipay.png) | [微信](http://hahack.com/images/misc/wechatpay.jpeg)）到本地进行扫描。

* 对于企业用户，建议[成为这个项目的 backer](https://opencollective.com/wukong-robot/contribute/tier/8131-sponsor)，您将可以把一个带链接的 logo 放在 wukong-robot 后台管理端的首页、捐赠页面以及 Github 项目首页中。

<p>
  <a href="https://opencollective.com/wukong-robot/sponsor/0/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/1/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/2/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/3/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/4/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/5/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/6/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/7/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/8/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/wukong-robot/sponsor/9/website" target="_blank"><img src="https://opencollective.com/wukong-robot/sponsor/9/avatar.svg"></a>
</p>

## 贡献

* 喜欢本项目请先打一颗星；
* 提 bug 请到 [issue 页面](https://github.com/wzpan/wukong-robot/issues)；
* 要贡献代码，欢迎 fork 之后再提 pull request；
* 插件请提交到 [wukong-contrib](https://github.com/wzpan/wukong-contrib) ；

## 联系

* wukong-robot 的主要开发者是 [潘伟洲](http://hahack.com) 。
* QQ 频道（推荐）：

使用 QQ 扫码加入：

![](https://wzpan-1253537070.cos.ap-guangzhou.myqcloud.com/misc/wukong-guild-qrcode-256.png)

* QQ 群：580447290（人数将满，为控制人数，需付费20元入群。微信或支付宝支付后，申请入群时贴上转账单号即可。**群收入的前一万元已无偿捐赠给[壹基金等公益项目](https://hahack-1253537070.cos.ap-chengdu.myqcloud.com/images/donate.png)**）。

| 支付宝 | 微信支付 |
| ------ | --------- |
| <img src="http://hahack.com/images/misc/alipay.png" height="248px" width="164px" title="支付宝" style="display:inherit;"/> | <img src="http://hahack.com/images/misc/wechatpay.jpeg" height="248px" width="164px" title="微信支付" style="display:inherit;"/> |

如果以上的图裂了，可以下载图片（[支付宝](http://hahack.com/images/misc/alipay.png) | [微信](http://hahack.com/images/misc/wechatpay.jpeg)）到本地进行扫描。

## 感谢

* 悟空的前身是 [dingdang-robot](https://github.com/dingdang-robot/dingdang-robot) 项目和 [jasper-client](https://github.com/jasperproject/jasper-client) 项目。感谢 [Shubhro Saha](http://www.shubhro.com/), [Charles Marsh](http://www.crmarsh.com/) and [Jan Holthuis](http://homepage.ruhr-uni-bochum.de/Jan.Holthuis/) 在 Jasper 项目上做出的优秀贡献；
* 感谢三咲智子提供了备选的后台管理端 Demo 体验地址。
* 感谢 aliciacai 贡献的 wukong-robot 图标。
* 感谢所有为[本项目](https://github.com/wzpan/wukong-robot/graphs/contributors)、 [wukong-contrib](https://github.com/wzpan/wukong-contrib/graphs/contributors) 项目以及[dingdang-robot](https://github.com/dingdang-robot/dingdang-robot/graphs/contributors) 项目做出过贡献的人！

## FAQ

- 我能否更换成其他唤醒词，而不是叫“孙悟空”？

  - 能。详见 [修改唤醒词](https://wukong.hahack.com/#/tips?id=_2-%e4%bf%ae%e6%94%b9%e5%94%a4%e9%86%92%e8%af%8d) 。
  
## 免责声明

* wukong-robot 只用作个人学习研究，如因使用 wukong-robot 导致任何损失，本人概不负责。
* 本开源项目与腾讯叮当助手及优必选悟空项目没有任何关系。
