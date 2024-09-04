
from datetime import datetime
import subprocess
import time


class Top:
    def __init__(self,process:subprocess.Popen):
        self.p = process
        self.total = []
    def get_data(self,pid ,duration =None):
        try:
            if duration is not None:
                start_time = datetime.now().timestamp()
            
            while True:
                if duration is not None and datetime.now().timestamp() - start_time > duration:
                    break
                # 读取一行输出
                self.dispose_data(pid)
        except KeyboardInterrupt:
            # 如果需要处理用户中断（例如使用 Ctrl+C），可以在这里添加代码
            print("Process was terminated by user.")
        finally:
            # 确保进程被正确终止
            self.p.terminate()
            self.p.wait()
        return self.total
    
    def dispose_data(self,pid):
        line = self.p.stdout.readline().decode("utf-8")
        if str(pid) in str(line):
            ret = line.split()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            self.total.append({'time':current_time,'RES':ret[1],'SHR':ret[2],'%CPU':ret[3],'%MEM':ret[4]})


class Cpu:
    def __init__(self,total_cpu,process_cpu,interval=1):
        self.total_cpu = total_cpu
        self.process_cpu = process_cpu
        self.interval = interval # 数据获取间隔

    '''
    计算某进程的cpu使用率
    100*( processCpuTime2 – processCpuTime1) / (totalCpuTime2 – totalCpuTime1) (按100%计算，如果是多核情况下还需乘以cpu的个数);
    cpukel cpu几核
    pid 进程id
    '''
    def cpu_rate(self):
        
        process_cputime_begain = self.process_cpu()
        time.sleep(self.interval)
        process_cputime2_end = self.process_cpu()

        total_cputime_begain = self.total_cpu()
        time.sleep(self.interval)
        total_cputime_end = self.total_cpu()
        

        # 按总量100%算原本应该除以cpu核数，现在是按100%*cpu核数
        cpu = 100 * (process_cputime2_end-process_cputime_begain) / (total_cputime_end - total_cputime_begain)
        # cpu = 100 * process_cputime_begain/total_cputime_begain
        cpu = round(cpu, 2)
        return cpu

    '''
    每一个cpu快照均
    '''
    # def total_cputime(self):
    #     user = nice = system = idle = iowait = irq = softirq = 0
    #     '''
    #     user:从系统启动开始累计到当前时刻，处于用户态的运行时间，不包含 nice值为负进程。
    #     nice:从系统启动开始累计到当前时刻，nice值为负的进程所占用的CPU时间
    #     system 从系统启动开始累计到当前时刻，处于核心态的运行时间
    #     idle 从系统启动开始累计到当前时刻，除IO等待时间以外的其它等待时间
    #     iowait 从系统启动开始累计到当前时刻，IO等待时间(since 2.5.41)
    #     irq 从系统启动开始累计到当前时刻，硬中断时间(since 2.6.0-test4)
    #     softirq 从系统启动开始累计到当前时刻，软中断时间(since 2.6.0-test4)
    #     stealstolen  这是时间花在其他的操作系统在虚拟环境中运行时（since 2.6.11）
    #     guest 这是运行时间guest 用户Linux内核的操作系统的控制下的一个虚拟CPU（since 2.6.24）
    #     '''
    #     for info in self.total_ret:
    #         if info == "cpu":
    #             user = self.total_ret[1]
    #             nice = self.total_ret[2]
    #             system = self.total_ret[3]
    #             idle = self.total_ret[4]
    #             iowait = self.total_ret[5]
    #             irq = self.total_ret[6]
    #             softirq = self.total_ret[7]
    #             result = int(user) + int(nice) + int(system) + int(idle) + int(iowait) + int(irq) + int(softirq)
    #             print("totalCpuTime" + str(result))
    #             return result


#     '''
#     每一个进程快照
#     '''
#     def process_cputime(self):
#         '''

#         pid     进程号
#         utime   该任务在用户态运行的时间，单位为jiffies
#         stime   该任务在核心态运行的时间，单位为jiffies
#         cutime  所有已死线程在用户态运行的时间，单位为jiffies
#         cstime  所有已死在核心态运行的时间，单位为jiffies
#         '''
#         utime = stime = cutime = cstime = 0
        
#         utime = self.pid_ret[13]
#         stime = self.pid_ret[14]
#         cutime = self.pid_ret[15]
#         cstime = self.pid_ret[16]
#         result = int(utime) + int(stime) + int(cutime) + int(cstime)
#         print(f'process time :{result}')
#         return result


    