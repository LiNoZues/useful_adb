import os
from libs.adb_base import AdbBase
from settings import aapt_pie_path,_aapt

class AAPT:
    def __init__(self,adb:AdbBase) -> None:
        self.adb = adb
    
    @staticmethod
    def chmod_aapt():
        """
        修改文件权限
        """
        CMD = f'sudo chmod 0755 {_aapt}'
        os.system(CMD)
    
    def check_aapt(self):
        """
        检查手机是否存在aapt-arm-pie
        """
        CMD = 'find /data/local/tmp/ -name aapt-arm-pie'
        ret = self.adb._cmd.get_stuout(cmd=CMD)
        if ret :
            return True
        else:
            return False
    
    def push_aapt_arm_pie(self):
        """
        将aapt-arm-pie上传到手机并赋予权限
        """
        target_path = '/data/local/tmp/'
        # step 1 上传
        self.adb.push(aapt_pie_path,target_path)
        # step 2 设置权限
        mode = '0755'
        path = os.path.join(target_path,'aapt-arm-pie')
        self.adb.chmod_file(path,mode)


if __name__ == '__main__':
    name ='global.longbridge.android.debug'
    ac = 'global.longbridge.android.LaunchActivity'
    xm = 'ff41f8c4'
    adb = AdbBase(filter)
    apt = AAPT(adb)
    print(apt.check_aapt())
    