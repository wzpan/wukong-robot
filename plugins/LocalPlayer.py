# -*- coding: utf-8-*-
import os
from robot import config, logging
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)

class MusicPlayer(object):

    def __init__(self, playlist, plugin):
        super(MusicPlayer, self).__init__()
        self.playlist = playlist
        self.plugin = plugin
        self.idx = 0
        self.volume = 0.6
        
    def play(self):
        logger.debug('MusicPlayer play')
        path = self.playlist[self.idx]
        if os.path.exists(path):
            self.plugin.play(path, False, self.next, self.volume)
        else:
            logger.error('文件不存在: {}'.format(path))    

    def next(self):
        logger.debug('MusicPlayer next')
        self.idx = (self.idx+1) % len(self.playlist)
        self.play()

    def prev(self):
        logger.debug('MusicPlayer prev')
        self.idx = (self.idx-1) % len(self.playlist)
        self.play()

    def stop(self):
        logger.debug('MusicPlayer stop')        

    def turnUp(self):
        if self.volume < 0.2:
            self.volume += 0.2
        self.play()

    def turnDown(self):
        if self.volume > 0:
            self.volume -= 0.2
        self.play()


class Plugin(AbstractPlugin):

    IS_IMMERSIVE = True  # 这是个沉浸式技能

    def __init__(self, con):
        super(Plugin, self).__init__(con)
        self.player = None

    def get_song_list(self, path):
        if not os.path.exists(path) or \
           not os.path.isdir(path):
            return []
        song_list = list(filter(lambda d: d.endswith('.mp3'), os.listdir(path)))        
        return [os.path.join(path, song) for song in song_list]

    def init_music_player(self):
        song_list = self.get_song_list(config.get('/LocalPlayer/path'))
        if song_list == None:
            logger.error('{} 插件配置有误'.format(self.SLUG))
        logger.info(song_list)
        return MusicPlayer(song_list, self)

    def handle(self, text, parsed):
        if not self.player:
            self.player = self.init_music_player()
        if self.nlu.hasIntent(parsed, 'MUSICRANK'):
            self.player.play()
        elif self.nlu.hasIntent(parsed, 'CHANGE_TO_NEXT'):
            self.say('下一首歌')
            self.player.next()
        elif self.nlu.hasIntent(parsed, 'CHANGE_TO_LAST'):
            self.say('上一首歌')
            self.player.prev()
        elif self.nlu.hasIntent(parsed, 'CHANGE_VOL'):
            word = self.nlu.getSlotWords(parsed, 'CHANGE_VOL', 'user_vd')[0]
            if word == '--LOUDER--':
                self.say('大声一点')
                self.player.turnUp()
            else:
                self.say('小声一点')
                self.player.turnDown()
        elif self.nlu.hasIntent(parsed, 'CLOSE_MUSIC') or self.nlu.hasIntent(parsed, 'PAUSE'):
            self.player.stop()
            self.clearImmersive()  # 去掉沉浸式
            self.say('退出播放')
        else:
            self.say('没听懂你的意思呢，要停止播放，请说停止播放')
            self.player.play()

    def restore(self):
        if self.player:
            self.player.play()

    def isValidImmersive(self, text, parsed):
        return any(self.nlu.hasIntent(parsed, intent) for intent in ['CHANGE_TO_LAST', 'CHANGE_TO_NEXT', 'CHANGE_VOL', 'CLOSE_MUSIC', 'PAUSE'])

    def isValid(self, text, parsed):
        return "本地音乐" in text

