# -*- coding: utf-8-*-

SLUG = "echo"
PRIORITY = 0

def handle(text, mic, profile, wxbot=None):
    """
        Reports the user input.

        Arguments:
        text -- user-input, typically transcribed speech
        mic -- used to interact with the user (for both input and output)
        profile -- contains information related to the user (e.g., phone
                   number)
        wxBot -- wechat robot
    """
    text = text.lower().replace('echo', '').replace(u'传话', '')
    mic.say(text)


def isValid(text):
    """
        Returns True if input is related to the time.

        Arguments:
        text -- user-input, typically transcribed speech
    """
    return any(word in text.lower() for word in ["echo", u"传话"])
