import subprocess
from loguru import logger as log
class Command:
    def __init__(self,device = None):
        self.device = device
    
    def live_subprocess(self,cmd,original_cmd = False):
        if original_cmd:
            _cmd = 'adb '+cmd
        else:
            _cmd = f'adb -s {self.device} shell '+cmd
        log.info(f"Runing Command:{_cmd}")
        process = subprocess.Popen(_cmd, shell=True, stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stdin=subprocess.PIPE)
        return process
        
    def get_stuout(self,cmd, line=False, original_outer=False,traget_deivce = True,original_cmd = False,duration = 10,logout= True):
        """
        line: True 按行切割   False 按空格切割
        original_outer: True 原始输出  False 解码后输出
        traget_deivce: True shell+目标设备  False shell
        original_cmd: True 原始命令  
        """
        # 不使用split进行字符串切割获取 防止不同手机 输出结果不同
        if original_cmd:
            _cmd = 'adb '+cmd
        else:
            if traget_deivce:
                _cmd = f'adb -s {self.device} shell '+cmd
            else:
                _cmd = f'adb shell '+cmd
        
        log.info(f"Runing Command:{_cmd}")
        outer, _ = subprocess.Popen(_cmd, shell=True, stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE,
                                    stdin=subprocess.PIPE).communicate(timeout=duration)
        if logout:
            log.info("Outer:{}".format(outer))
        if original_outer:
            return outer.decode('utf-8')
        # 解码 b'xxx'转换为字符串
        if not line:
            return [x.decode(encoding='utf8') for x in outer.split()]
        else:
            # 按行切割
            return list(filter(None, [x.decode(encoding='utf8') for x in outer.splitlines()]))

    