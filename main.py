from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess
import time
import setting
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


go_hour = int(setting.go_hour) - 1
back_hour = int(setting.back_hour)
directory = setting.directory
sender = setting.sender
psw = setting.psw
receive = setting.receive
screen_dir = setting.screen_dir


class dingDing:
    def __init__(self, directory):
        self.directory = directory
        # 点亮屏幕
        self.adbpower = '"%s\\adb" shell input keyevent 26' % directory
        # 滑屏解锁
        # self.adbclear = '"%s\\adb" shell input swipe %s' % (directory, config.light_position)
        # 启动钉钉应用
        self.adbopen_dingding = '"%s\\adb" shell monkey -p com.alibaba.android.rimet -c android.intent.category.LAUNCHER 1' % directory
        # 关闭钉钉
        self.adbkill_dingding = '"%s\\adb" shell am force-stop com.alibaba.android.rimet' % directory
        # 返回桌面
        self.adbback_index = '"%s\\adb" shell input keyevent 3' % directory
        # 点击工作
        self.adbselect_work = '"%s\\adb" shell input tap %s' % (directory, setting.work_position)
        # 点击考勤打卡
        self.adbselect_playcard = '"%s\\adb" shell input tap %s' % (directory, setting.check_position)
        # 点击下班打卡
        self.adbclick_playcard = '"%s\\adb" shell input tap %s' % (directory, setting.play_position)
        # 设备截屏保存到sdcard
        self.adbscreencap = '"%s\\adb" shell screencap -p sdcard/screen.png' % directory
        # 传送到计算机
        self.adbpull = '"%s\\adb" pull sdcard/screen.png %s' % (directory, screen_dir)
        # 删除设备截屏
        self.adbrm_screencap = '"%s\\adb" shell rm -r sdcard/screen.png' % directory

    def open_dingding(self):
        operation_list = [self.adbopen_dingding]
        for operation in operation_list:
            process = subprocess.Popen(operation, shell=False, stdout=subprocess.PIPE)
            process.wait()
        # 确保完全启动，并且加载上相应按键
        time.sleep(20)
        print("1. 钉钉已开启")

    def close_dingding(self):
        operation_list = [self.adbback_index, self.adbkill_dingding]
        for operation in operation_list:
            process = subprocess.Popen(operation, shell=False, stdout=subprocess.PIPE)
            process.wait()
        print("4. 钉钉已关闭")

    # 上班(极速打卡)
    def goto_work(self):
        self.open_dingding()
        self.screencap()
        self.send_email()
        self.close_dingding()
        print("5. 上班打卡成功")

    def off_work(self):
        self.open_dingding()
        operation_list = [self.adbselect_work, self.adbselect_playcard, self.adbclick_playcard]
        for operation in operation_list:
            process = subprocess.Popen(operation, shell=False, stdout=subprocess.PIPE)
            process.wait()
            print('> 工作台/考勤/打卡 等待10s')
            time.sleep(10)
        self.screencap()
        self.send_email()
        self.close_dingding()
        print("5. 下班打卡成功")

    def screencap(self):
        operation_list = [self.adbscreencap, self.adbpull, self.adbrm_screencap]
        for operation in operation_list:
            process = subprocess.Popen(operation, shell=False, stdout=subprocess.PIPE)
            process.wait()
        print("2. 屏幕已截取")

    @staticmethod
    def send_email():
        now_time = datetime.datetime.now().strftime("%H:%M:%S")
        message = MIMEMultipart('related')
        subject = now_time + '打卡'
        message['Subject'] = subject
        message['From'] = "日常打卡"
        message['To'] = receive
        content = MIMEText('<html><body><img src="cid:imageid" alt="imageid"></body></html>', 'html', 'utf-8')
        message.attach(content)
        file = open(screen_dir, "rb")
        img_data = file.read()
        file.close()
        img = MIMEImage(img_data)
        img.add_header('Content-ID', 'imageid')
        message.attach(img)
        try:
            server = smtplib.SMTP_SSL("smtp.qq.com", 465)
            server.login(sender, psw)
            server.sendmail(sender, receive, message.as_string())
            server.quit()
            print("3. 邮件已发送")
        except smtplib.SMTPException as e:
            print(e)


def job1():
    print("=============上班打卡==============")
    dingDing(directory).goto_work()


def job2():
    print("=============下班打卡==============")
    dingDing(directory).off_work()


# BlockingScheduler
if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(job1, 'cron', hour=8, minute=33)
    scheduler.add_job(job2, 'cron', hour=23, minute=30)
    scheduler.start()
