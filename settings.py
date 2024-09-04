import platform
import os
root_path = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(root_path,'static')
system = platform.system()
# todo:支持电脑不存在adb的情况
if system == 'Windows':
    my_adb = os.path.join(static_path,'windows')
    # adb = os.path.join(my_adb,'adb.exe')
    _aapt = os.path.join(my_adb,'aapt.exe')
    _filter = 'findstr'
elif system == 'Darwin':
    my_adb =os.path.join(static_path,'mac')
    # adb = os.path.join(my_adb,'adb')
    _aapt = os.path.join(my_adb,'aapt')
    _filter = 'grep'
else:
    raise Exception('暂不支持Linux')
aapt_pie_path = os.path.join(static_path,'aapt-arm-pie')
logcat_path = os.path.join(os.path.expanduser('~'), 'Desktop') # 默认桌面路径，跨平台兼容
