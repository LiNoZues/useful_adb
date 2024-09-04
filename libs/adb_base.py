import datetime
import math
import os
import re
import subprocess
from loguru import logger as log
from libs.perf.fps import FPS
from settings import _filter,aapt_pie_path,logcat_path
from libs.command import Command
from libs.keyevent import KeyBoardEvent as key
from libs.perf.cpu_and_memery import Cpu, Top

class AdbBase:
    def __init__(self,_filter,device=None,package_name = None,activity = None,auto=True):
        self.device = device
        self._filter = _filter
        self.package_name = package_name
        self.activity = activity # 保存的是用于启动的activity
        self._cmd = Command(device)
        if self.device is None:
            self.init_device()
        if auto and package_name is None and activity is None:
            self.app_package_name_activity()
        self.process_id()
        self.sdk_version()

    def init_device(self):
        self.device = self.devices_list()[0]
        # update _cmd
        self._cmd = Command(self.device)

    def devices_list(self):
        """
        获取设备列表
        """
        CMD = 'devices'
        ret = self._cmd.get_stuout(cmd=CMD,line=True,original_cmd=True)
        if len(ret) <= 1:
            log.error('获取设备列表失败')
            
        else:
            return [device.split()[0] for device in ret[1:]]
    
    def awake(self):
        """
        唤醒屏幕
        """
        CMD = 'input keyevent {}'.format(key.AWAKE)
        self._cmd.get_stuout(cmd=CMD)
    
    def turn_off(self):
        """
        熄屏
        """
        CMD = 'input keyevent {}'.format(key.TURN_OFF)
        self._cmd.get_stuout(cmd=CMD)

    def app_package_name_activity(self):
        """
        获取当前app的包名和app启动的activity
        """
        CMD = 'dumpsys activity recents | {} intent='.format(_filter)
        ret = self._cmd.get_stuout(cmd=CMD,line=True)[0]
        pat = re.compile('cmp=(.*)/(.*)')
        try:
            group = pat.findall(ret)[0]
            self.package_name = group[0]
            self.activity = group[1]
        except IndexError:
            log.warning('获取app的包名和app启动的activity失败')
            raise Exception('请打开app后重试')
        else:
            # (package_name,activity)
            return group

    def top_app_package_name_activity(self)->tuple:
        """
        获取当前app的包名和app当前界面的activity
        """
        CMD = f'dumpsys window | {_filter} mCurrentFocus'
        ret = self._cmd.get_stuout(cmd=CMD)[2].strip().replace('}','').split('/')
        return tuple(ret)
    
    def surfaceview_view(self,package_name=None):
        """
        获取 surfaceview 
        """
        if package_name is None:
            package_name = self.top_app_package_name_activity()[0]
        CMD = f'dumpsys SurfaceFlinger --list | {_filter} {package_name}'
        ret = self._cmd.get_stuout(cmd=CMD,line=True)
        activity_line = ''
        for line in ret:
            if line.startswith('SurfaceView') and line.find(package_name) != -1:
                activity_line = line.strip()
        if activity_line:
            if activity_line.find(' ')  != -1:      
                activity_name = activity_line.split(' ')[2]
            else:
                activity_name = activity_line.replace('SurfaceView','').replace('[','').replace(']','')    
        else:
            activity_name = ret[-1]
            if not activity_name.__contains__(package_name):
                log.error('get activity name failed, Please provide SurfaceFlinger --list information to the author')
                return 
        # package_name/activity#xxx
        return activity_name

    def process_id(self,package_name =None,return_all = False):
        """
        获取对应应用进程id
        """
        if package_name is None:
            package_name = self.package_name
        CMD = f"ps | {_filter} {package_name} | awk '{{print $2}}'"
        ret = self._cmd.get_stuout(cmd=CMD,line=True)
        if len(ret) > 1 :
            log.debug(f'当前应用有多个进程')
        if return_all:
            return ret
        else:
            self.pid = ret[0]
            return self.pid
    
    def process_uid(self,pid=None):
        """
        获取对应进程uid
        """
        if pid is None:
            pid = self.pid
        CMD = "cat /proc/{}/status | {} Uid | awk '{{print $2}}'".format(pid,_filter)
        ret = self._cmd.get_stuout(cmd=CMD)
        uid = ret[0]
        return uid

    
    def monkey_pid(self):
        """
        获取monkey进程id
        """
        CMD = f'ps | {_filter} monkey'
        ret = self._cmd.get_stuout(cmd=CMD)
        if ret:
            pid = ret[1]
            return pid
        else:
            log.error('没有找到monkey进程')

    def logcat_id(self):
        '''
        获取logcat 进程号
        '''
        cmd = f'ps | {_filter} logcat'
        res = self._cmd.get_stuout(cmd,line=True)
        if not res:
            log.warning('没有找到logcat进程')
            return 
        if 'system' in res[0]:
            return res[1:]
        else:
            return res
    
    def close_logcat(self):
        '''
        关闭logcat
        '''
        _id = self.logcat_id()
        cmd = f'kill {_id}'
        self._cmd.get_stuout(cmd)
    
    def logcat(self,levle='W',save_path = None,duration = None):
        """
        locat 获取日志
        """
        # Error = E、Warning = W、Info = I、Debug = D
        CLEAR_CMD = 'logcat -c'
        # 清除logcat缓存
        self._cmd.get_stuout(CLEAR_CMD)
        # downlodad logcat
        if save_path is None:
            save_path = os.path.join(logcat_path,datetime.datetime.now().strftime('%Y%m%d%H%M%S')+'.log')
        cmd = f"logcat *:{levle} | {_filter} {self.package_name} > {save_path}"
        if duration is not None:
            try:
                self._cmd.get_stuout(cmd,duration = duration)
            except subprocess.TimeoutExpired:
                log.info('获取logcat结束')
        else:
            try:    
                p = self._cmd.live_subprocess(cmd)
            except KeyboardInterrupt:
                log.warning("Process was terminated by user.")
            finally:
                # 确保进程被正确终止
                p.terminate()
                p.wait()
            
    def system_version(self):
        """
        获取系统版本
        """
        CMD = 'getprop ro.build.version.release'
        ret = self._cmd.get_stuout(cmd=CMD,original_outer=True)
        return ret
    
    def phone_brand(self):
        """
        获取手机品牌
        """
        CMD = 'getprop ro.product.brand'
        ret = self._cmd.get_stuout(cmd=CMD,original_outer=True)
        return ret

    def phone_model(self):
        """
        获取手机型号
        """
        CMD = 'getprop ro.product.model'
        ret = self._cmd.get_stuout(cmd=CMD,original_outer=True)
        return ret

    def phone_memory(self):
        """
        获取内存信息
        """
        CMD = f'cat /proc/meminfo | {_filter} MemTotal'
        ret = self._cmd.get_stuout(cmd=CMD) # ['MemTotal:', '5863120', 'kB']
        mem = str(math.ceil(int(ret[1]) / 1024/1024)) + 'GB'
        return mem

    def phone_cpu(self):
        """
        获取cpu信息
        """
        CMD = f'cat /proc/cpuinfo | {_filter} processor'
        ret = self._cmd.get_stuout(cmd=CMD,line=True)
        cpu = len(ret)
        return str(cpu)+"核"
    
    def phone_resolution(self):
        """
        获取手机分辨率
        """
        CMD = f"wm size | {_filter} Physical"
        ret = self._cmd.get_stuout(cmd=CMD)
        return ret[-1]

    def phone_network(self):
        """
        获取手机网络
        """
        CMD = f'dumpsys connectivity | grep NetworkAgentInfo'
        ret = self._cmd.get_stuout(cmd=CMD)
        net_type = ret[2].split("{")[1]
        # WIFI / MOBILE[LTE]
        return net_type
    
    def third_app_name(self):
        """
        获取第三方应用
        """
        CMD = f'pm list packages -3'
        ret = self._cmd.get_stuout(cmd=CMD)
        return ret
    def third_apk_path(self):
        """
        获取第三方应用 .apk路径和package_name
        """
        CMD = f'pm list packages -3 -f'
        ret = self._cmd.get_stuout(cmd=CMD)
        result = dict()
        pat = re.compile('(/.*/base\.apk)=(.*)')
        for item in ret:
            group = pat.findall(item)[0]

            result[group[1]] = group[0]
        return result
    
    def install_application(self,apk_path):
        """
        安装应用
        """
        # -g 给权限
        CMD = f'install -g {apk_path}'
        ret = self._cmd.get_stuout(cmd=CMD,original_outer=True)
        if 'success' in ret.lower():
            return True
        else:
            log.error('APP install Failed')
            return False
    
    def uninstall_application(self,package_name):
        """
        卸载应用
        """
        CMD = f'uninstall {package_name}'
        ret = self._cmd.get_stuout(cmd=CMD,original_outer=True)
        if 'success' in ret.lower():
            return True
        else:
            log.error('APP uninstall Failed')
            return False
    def open_application(self,package_name,activity):
        """
        打开应用
        """
        CMD = f'am start -W -n {package_name}/{activity}'
        ret = self._cmd.get_stuout(cmd=CMD,line=True)
        if 'Complete' in ret[-1]:
            return True,ret
        else:
            log.error('APP open Failed')
            return False
    
    def close_application(self,package_name = None):
        """
        关闭应用
        """
        if package_name is None:
            package_name = self.package_name
        CMD = f'am force-stop {package_name}'
        self._cmd.get_stuout(cmd=CMD,original_outer=True)
    
    def back_home(self):
        """
        返回桌面
        """
        CMD = f'input keyevent {key.HOME}'
        self._cmd.get_stuout(cmd=CMD)
    
    def batery(self):
        """
        获取电量
        """
        CMD = f'dumpsys battery | {_filter} level'
        ret = self._cmd.get_stuout(cmd=CMD)
        return ret[1]
    
    def screenshot(self, name)->str:
        """
        截图报保存到sd卡
        """
        save_path = f'/sdcard/{name}.png'
        CMD = f'screencap -p {save_path}'
        self._cmd.get_stuout(cmd=CMD)
        return save_path
    
    def screencap_out(self,save_path):
        """
        截图保存到电脑
        """
        CMD = f'exec-out screencap -p {save_path}'
        self._cmd.get_stuout(cmd=CMD)
        return save_path
    
    def pull(self,source_path,target_path):
        """
        从设备拉取文件
        """
        CMD = f'pull {source_path} {target_path}'
        self._cmd.get_stuout(cmd=CMD)

    def sdk_version(self):
        """
        获取sdk版本
        """
        CMD = f'getprop ro.build.version.sdk'
        ret = self._cmd.get_stuout(cmd=CMD)
        self._sdk_version = int(ret[0])
        return self._sdk_version
        
    def push(self,source_path,target_path):
        """
        向设备推送文件
        """
        CMD = f'push {source_path} {target_path}'
        self._cmd.get_stuout(cmd=CMD)
    
    def chmod_file(self,mode,source_path):
        """
        修改文件权限
        """
        # mode = 权限
        CMD = f'chmod {mode} {source_path}'
        self._cmd.get_stuout(cmd=CMD)

    def flow(self):
        """
        获取流量
        """
        CMD = f'dumpsys netstats | {_filter} uid'
        ret = self._cmd.get_stuout(cmd=CMD)
        return ret
    
    def top_for_mem_and_cpu_info(self,pid = None,interval = 1,duration = None):
        """
        通过top获取进程内存和cpu占用
        """
        """
        https://www.cnblogs.com/yc-c/p/9957959.html
        PID — 进程id
        USER — 进程所有者
        PR — 进程优先级
        NI — nice值。负值表示高优先级，正值表示低优先级
        VIRT — 进程使用的虚拟内存总量，单位kb。VIRT=SWAP+RES
        RES — 进程使用的、未被换出的物理内存大小，单位kb。RES=CODE+DATA
        SHR — 共享内存大小，单位kb
        S — 进程状态。D=不可中断的睡眠状态 R=运行 S=睡眠 T=跟踪/停止 Z=僵尸进程
        %CPU — 上次更新到现在的CPU时间占用百分比
        %MEM — 进程使用的物理内存百分比
        TIME+ — 进程使用的CPU时间总计，单位1/100秒
        COMMAND — 进程名称（命令名/命令行）
        """
        if pid is None:
            pid = self.pid
        CMD = f'top -d {interval} -p {pid} -o PID -o RES -o SHR -o %CPU -o %MEM'
        process = self._cmd.live_subprocess(cmd=CMD)
        ret = Top(process).get_data(pid,duration)
        log.debug(ret)
        return ret
    
    def memory_info(self,package_name = None):
        """
        获取内存占用信息
        """
        if package_name is None:
            package_name = self.package_name
        CMD = f'dumpsys meminfo {package_name} | {_filter} TOTAL'
        # 返回的数据单位是kb
        ret = self._cmd.get_stuout(cmd=CMD,line=True)[0] 
        # 转换成MB
        pss_mem = math.ceil(int(ret.split()[1])/1024)
        return pss_mem

    def proc_for_cpu_info(self,pid=None):
        """
        通过proc/stat获取cpu占用率
        """
        if pid is None:
            pid = self.pid
        # TOTAL_CMD = f'cat /proc/stat'
        TOTAL_CMD = "cat /proc/stat | grep '^cpu' | awk '{sum=0; for (i=2; i<=8; i++) sum+=$i} END {print sum}'"
        PID_CMD = f"cat /proc/{pid}/stat | awk '{{sum=0; for (i=14; i<=17; i++) sum+=$i}} END {{print sum}}'"
            
        total_cpu_time = lambda : int(self._cmd.get_stuout(cmd=TOTAL_CMD)[0])
        pid_time = lambda: int(self._cmd.get_stuout(cmd=PID_CMD)[0])
        cpu_percent = Cpu(total_cpu=total_cpu_time,process_cpu=pid_time).cpu_rate()
        log.debug(f'CPU percents: {cpu_percent}')
        return cpu_percent

    def gfx_for_fps(self,package_name = None):
        """
        通过dumpsys gfxinfo获取fps
        """
        if package_name is None:
            package_name = self.package_name
        CMD = f'dumpsys gfxinfo {package_name} framestats'
        ret = self._cmd.get_stuout(cmd=CMD,line=True,logout=False)
        return ret

    def check_dev_gpu(self):
        """
        检查开发者选项-GPU呈现模式分析是否打开
        """
        CMD = f'getprop debug.hwui.profile'
        res = self._cmd.get_stuout(cmd=CMD)
        if not res:
            log.warning(f'{self.device} 无法获取帧率数据, 请打开“开发者选项-GPU呈现模式分析”开关')
    
    def open_dev_gpu(self):
        """
        打开开发者选项-GPU呈现模式分析
        """
        CMD = 'setprop debug.hwui.profile true'
        self._cmd.get_stuout(cmd=CMD)
    
    def clear_surfaceflinger_latency_data(self):
        """ 
        清除SurfaceFlinger的延迟数据    
        """
        CMD = 'dumpsys SurfaceFlinger --latency-clear'
        res = self._cmd.get_stuout(cmd=CMD)
        if not len(res) :
            return True
        else:
            return False
    
    def refresh_period_time(self,focuse_activity = None):
        """ 
        获取刷新间隔时间    
        """
        if focuse_activity is None:
            focuse_activity = self.top_app_package_name_activity()[1]
        CMD = f'dumpsys SurfaceFlinger --latency {focuse_activity}'
        res = self._cmd.get_stuout(cmd=CMD,line=True)
        return res[0]

    def surfaceflinger_latency_for_fps(self,surface_view = None):
        """ 
        获取fps通过SurfaceFlinger的延迟数据    
        """
        if surface_view is None:
            surface_view = self.surfaceview_view()
        CMD = f'dumpsys SurfaceFlinger --latency {surface_view}'
        res = self._cmd.get_stuout(cmd=CMD,line=True,logout=False)
        return res
    
    def fps_info(self,jank_threshold = 166):
        """ 
        获取fps信息
        """
        fps = FPS(jank_threshold=jank_threshold,package_name=self.package_name,sdk_version=self._sdk_version)
        if self._sdk_version > 26:
            frame_data = self.gfx_for_fps()
            body = {'period_time':self.refresh_period_time(),'frame_data':frame_data}
        else:
            frame_data = self.surfaceflinger_latency_for_fps()
            body = {'frame_data':frame_data}
        return fps.get_fps(**body)
        


if __name__ == '__main__':
    import time
    name ='global.longbridge.android.debug'
    ac = 'global.longbridge.android.LaunchActivity'
    xm = 'ff41f8c4'
    adb = AdbBase(_filter)
    # print(adb.sdk_version())
    # adb.gfx_for_fps()
    ret = adb.fps_info()
    print(ret)
    # data = adb.memory_info()
    # print(pid)
    
    # try:
    
    #     while True:
    #         # 读取一行输出
    #         line = p.stdout.readline()
    #         if line:
    #             print('********************************')
    #             print(line.strip())  # 打印读取到的行，并去除两端的空白字符
    # except KeyboardInterrupt:
    #     # 如果需要处理用户中断（例如使用 Ctrl+C），可以在这里添加代码
    #     print("Process was terminated by user.")
    # finally:
    #     # 确保进程被正确终止
    #     p.terminate()
    #     p.wait()
        
    # print(adb.devices_list())
    
    # print(adb.get_logcat_id())
    # print(adb.open_application(name,ac))