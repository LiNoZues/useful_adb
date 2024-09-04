import os
import re
import zipfile
import subprocess
from libs.android_dom import manifest
from settings import _aapt
from libs._aapt import AAPT
class APK:
    def __init__(self,apk_path = None):
        self.path = apk_path
        self.apk_info, self.apk_zip = self.apk_parse()

    def apk_parse(self):
        """
        解析apk 信息
        :param apk_path: apk路径
        :return:
        """
        # AAPT.chmod_aapt()
        command = f'{_aapt} dump badging {self.path}'
        res = subprocess.run(command, shell=True, stdout=subprocess.PIPE).stdout.decode('utf8')
        apk_zip = zipfile.ZipFile(self.path)
        return res, apk_zip

    def get_packageName(self):
        try:
            pat = re.compile(r"package: name='(\S+)'", re.M)
            package_name = pat.findall(self.apk_info)[0]  # 返回[(name,code,v_name)]
            return package_name
        except Exception as e:
            try:
                return manifest(self.apk_zip).package_name
            except:
                cmd = 'del {}'.format(self.path).replace('/', '\\')
                os.popen(cmd)  # 删除apk
                raise Exception('获取package_name失败')

    def get_versionCode(self):
        pat = re.compile(r"versionCode='(\d+)'", re.M)
        version_code = pat.findall(self.apk_info)[0]  # 返回[(name,code,v_name)]
        return version_code

    def get_versionName(self):
        pat = re.compile(r"versionName='(\S*)'", re.M)
        version_name = pat.findall(self.apk_info)[0]  # 返回[(name,code,v_name)]
        return version_name

    def get_activity(self):
        try:
            app_activity = re.compile(r"launchable-activity: name='(.*)'.*label", re.M).findall(self.apk_info)[
                0].strip()
            return app_activity
        except:
            try:
                return manifest(self.apk_zip).main_activity
            except:
                cmd = 'del {}'.format(self.path).replace('/', '\\')
                os.popen(cmd)  # 删除apk
                raise Exception('获取Activity失败')

    def get_name(self):
        app_name = re.compile(r"application-label:'(.*)'", re.M).findall(self.apk_info)[0].strip()
        return app_name

    def get_icon(self, save_path):
        """
        :param save_path: 存储路径
        :return:
        """
        pat = re.compile(r"application-icon-\d.*:'(.*)'", re.M)
        icon_path = pat.findall(self.apk_info)[0]
        icon = self.apk_zip.read(icon_path)
        with open(save_path, 'wb') as f:
            f.write(icon)
if __name__ == '__main__':
    path = '/Users/cz/Downloads/Ant_Mo_Bank_release_1.5.1.00000070_50-sit-release.apk'
    pt = APK(path)
    # with open('C:\Users\olay_Czz\Desktop\ccc\main.xml','wb') as f:
    #     f.write(pt.apk_zip)
    # zipFile = zipfile.ZipFile(s.apk_path)
    # for file in zipFile.namelist():
    #     zipFile.extract(file, r'C:\Users\olay_Czz\Desktop\ccc\tt')
    # zipFile.close()
    a = pt.get_activity()
    b = pt.get_packageName()
    print(a,b)
    # os.system('adb shell am start -W -n {}/{}'.format(a,b))
