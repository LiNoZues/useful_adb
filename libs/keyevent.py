from typing import Any


class KeyMap:
    def __init__(self,key,description):
        self.key = key
        self.description = description
    def __repr__(self):
        return self.key

class KeyBoardEvent:
    AWAKE = KeyMap('224','唤醒屏幕')
    TURN_OFF = KeyMap('223','熄灭屏幕')
    HOME = KeyMap('3','回到桌面')


if __name__ == '__main__':
    k = KeyBoardEvent.AWAKE
    a = k
    print(a)