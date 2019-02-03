# -*- coding: utf-8-*-
from robot import ASR, TTS, AI, Player, config, constants, utils
from snowboy import snowboydecoder

player, asr, ai, tts = None, None, None, None

def init():
    global asr, ai, tts    
    asr = ASR.get_engine_by_slug(config.get('asr_engine', 'tencent-asr'))
    ai = AI.get_robot_by_slug(config.get('robot', 'tuling'))
    tts = TTS.get_engine_by_slug(config.get('tts_engine', 'baidu-tts'))

def converse(fp):
    global player, asr, ai, tts
    try:
        snowboydecoder.play_audio_file(constants.getData('beep_lo.wav'))
        print("converting audio to text")        
        query = asr.transcribe(fp)
        utils.check_and_delete(fp)        
        msg = ai.chat(query)        
        voice = tts.get_speech(msg)
        player = Player.getPlayerByFileName(voice)
        player.play(voice, True)
    except ValueError as e:
        logger.critical(e)
        utils.clean()

def play(voice):
    player = Player.getPlayerByFileName(voice)
    player.play(voice)

def stop():
    global player
    if player is not None and player.is_playing():
        player.stop()
        player = None
