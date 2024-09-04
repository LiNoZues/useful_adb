import re
import time
from libs.adb_base import AdbBase

class Launch:
    """
    启动app
    """
    def __init__(self,adb:AdbBase) -> None:
        self.adb = adb
    # 获取启动时间信息
    def get_times(self,context):
        # TotalTime:应用自身启动耗时=ThisTime+应用application等资源启动时间
        # WaitTime:系统启动应用耗时=TotalTime+系统资源启动时间
        # 时间单位:ms
        lines = context
        totaltime = waittime = warn =''
        for line in lines:
            if 'WaitTime' in line:
                waittime = line.split()[1]
            if 'TotalTime' in line:
                totaltime = line.split()[1]
            if 'Warning' in line:
                warn = line
        return totaltime, waittime, warn
    
    def cold_process(self, package_name, activity):
        """
        冷启动
        """
        success,context = self.adb.open_application(package_name, activity)
        if not success:
            raise Exception('Failed to open')
        res = self.get_times(context)
        time.sleep(2)
        self.adb.close_application(package_name)
        return res
    
    def hot_process(self, package_name, activity):
        """
        热启动 - 后台唤醒
        """
        # cold open
        self.adb.open_application(package_name, activity)
        time.sleep(2)
        self.adb.back_home()
        time.sleep(2)
        # hot open
        _,context = self.adb.open_application(package_name, activity)
        res = self.get_times(context)
        # 热启动只有 waittime
        return res

if __name__ == '__main__':
    from settings import _filter
    name ='global.longbridge.android.debug'
    ac = 'global.longbridge.android.LaunchActivity'
    adb = AdbBase(_filter)
    launch = Launch(adb)
    res = launch.hot_process(name,ac)
    print(res)