from abc import ABCMeta, abstractmethod

class AbstractPlugin(metaclass=ABCMeta):
    """ 技能插件基类 """

    SLUG = 'AbstractPlugin'
    IS_IMMERSIVE = False

    def __init__(self, con):
        if self.IS_IMMERSIVE is not None:
            self.isImmersive = self.IS_IMMERSIVE
        else:
            self.isImmersive = False
        self.priority = 0
        self.con = con
        self.nlu = self.con.nlu

    def play(self, src, delete=False, onCompleted=None, volume=1):
        self.con.play(src, delete, onCompleted, volume)

    def say(self, text, cache=False, onCompleted=None):
        self.con.say(text, cache=cache, plugin=self.SLUG, onCompleted=onCompleted)

    def activeListen(self):
        return self.con.activeListen()

    def clearImmersive(self):
        self.con.setImmersiveMode(None)

    @abstractmethod
    def isValid(self, query, parsed):
        """
        是否适合由该插件处理

        参数：
        query -- 用户的指令字符串
        parsed -- 用户指令经过 NLU 解析后的结果

        返回：
        True: 适合由该插件处理
        False: 不适合由该插件处理
        """
        return False

    @abstractmethod
    def handle(self, query, parsed):
        """
        处理逻辑

        参数：
        query -- 用户的指令字符串
        parsed -- 用户指令经过 NLU 解析后的结果
        """
        pass

    def isValidImmersive(self, query, parsed):
        """
        是否适合在沉浸模式下处理，
        仅适用于有沉浸模式的插件（如音乐等）
        当用户唤醒时，可以响应更多指令集。
        例如：“"上一首"、"下一首" 等
        """
        return False

    def restore(self):
        """
        恢复当前插件，
        仅适用于有沉浸模式的插件（如音乐等）
        当用户误唤醒或者唤醒进行闲聊后，
        可以自动恢复当前插件的处理逻辑
        """
        return
    
