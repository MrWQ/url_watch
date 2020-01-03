#!/usr/bin/python3
# -*- coding: utf-8 -*-
import linecache
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import requests
import os
from apscheduler.schedulers.blocking import BlockingScheduler


requests.adapters.DEFAULT_RETRIES = 5           # 增加重连次数
results_dir = 'results'                         # 文件夹名称
config_file = 'config.txt'                      # 配置文件，包含发邮件的邮箱
log_file = 'log.txt'                            # log记录文件
url_file = 'url.txt'                            # url列表文件
mail_file = 'mail.txt'                          # 邮箱列表文件
my_sender = ""                                  # 发件人邮箱账号
my_pass = ""                                    # 发件人授权码
receivers = []                                  # 收件人邮箱账号
send_name = ""                                  # 发件名
send_subject = ""                               # 发件主题
msg = ""                                        # 邮件内容提示
url_list = []                                   # url测试列表


# 初始化
def init():
    encode_file(config_file)
    encode_file(url_file)
    encode_file(mail_file)
    global my_sender
    global my_pass
    global receivers
    global send_name
    global send_subject
    global msg
    global url_list
    my_sender = linecache.getline(config_file, 1).strip()       # 发件人邮箱账号
    my_pass = linecache.getline(config_file, 2).strip()         # 发件人授权码
    receivers = check_mail(mail_file)                           # 收件人邮箱账号
    send_name = linecache.getline(config_file, 3).strip()       # 发件名
    send_subject = linecache.getline(config_file, 4).strip()    # 发件主题
    msg = linecache.getline(config_file, 5).strip() + '\n'      # 邮件内容提示
    url_list = linecache.getlines(url_file)                     # url测试列表
    # makedir(results_dir)


def makedir(dir_name):
    if os.path.lexists(dir_name):
        os.chdir(dir_name)
    else:
        os.makedirs(dir_name)
        os.chdir(dir_name)


# 打印log
def log(string):
    with open(log_file, 'a', encoding='utf-8') as logf:
        logf.write('[{}] {}\n'.format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), string))


# 将文件编码改为utf-8
# 改变文件编码utf-8 防止gbk编码文件无法打开
def encode_file(path):
    # 改变文件编码utf-8 防止gbk编码文件无法打开
    fp = open(path, 'rb')
    fps = fp.read()
    fp.close()
    try:
        fps = fps.decode('utf-8')
    except:
        fps = fps.decode('gbk')
    fps = fps.encode('utf-8')
    fp = open(path, 'wb')
    fp.write(fps)
    fp.close()


def url_test():
    log("url_watch start")
    print("url_watch start")
    now = datetime.datetime.now()  # 获取当前时间对象
    name = now.strftime("%Y-%m-%d+%H-%M")
    url_result = str(name) + 'urlresults.txt'
    url_code = str(name) + 'code.txt'
    GHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Connection': 'close'
    }
    if url_list == []:
        print('获取url列表失败！检查同文件夹下是否有{}，以及{}文件中是否有url'.format(url_file, url_file))
        log('获取url列表失败！检查同文件夹下是否有{}，以及{}文件中是否有url'.format(url_file, url_file))
    code_results = []
    with open(url_result, 'w', encoding='utf-8') as fu:
        with open(url_code, 'w', encoding='utf-8') as fc:
            for u in url_list:
                if '://' in u:
                    pass
                else:
                    u = 'http://' + u
                u = u.replace('\n', '')
                u = u.replace('\t', '')
                u = u.replace(' ', '')
                u = u.replace('Http://', 'http://')
                u = u.replace('Https://', 'https://')
                try:
                    session = requests.session()
                    session.keep_alive = False
                    code = session.head(url=u, headers=GHeaders, timeout=10, verify=False, allow_redirects=True).status_code
                except Exception as e:
                    print(e)
                    code = '超时'
                # 4xx和5xx 状态码用get方法重新请求验证，某些平台可能禁用head方法
                # 如果不为2xx,用get请求
                if str(code)[0] != '2':
                    try:
                        code = session.get(url=u, headers=GHeaders, timeout=10, verify=False).status_code
                    except Exception as e:
                        print(e)
                        code = '超时'
                print(u, code)
                fu.write(u + '\t' + str(code))
                fu.write('\n')
                fc.write(str(code))
                fc.write('\n')
                code_results.append(code)
    log("url_watch end")
    print("url_watch end")
    return code_results


def fu_jian(name):
    # 构造附件1，传送当前目录下的 test.txt 文件
    att = MIMEText(open(name, 'rb').read(), 'base64', 'utf-8')
    att["Content-Type"] = 'application/octet-stream'
    # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
    att["Content-Disposition"] = 'attachment; filename=' + name
    return att


# 检查邮箱地址,返回正确邮箱地址
def check_mail(file):
    mail_list = []
    encode_file(file)
    mail_results = linecache.getlines(file)
    for mail in mail_results:
        mail = mail.strip()
        if '@' in mail:
            mail_list.append(mail)
    # print('收件人', mail_list)
    # log('收件人 {}'.format(mail_list))
    return mail_list


def send_mail(send_name, send_subject, send_msg, fujian_list):
    print("开始发送邮件")
    log("开始发送邮件")
    # 第三方 SMTP 服务
    # 邮箱	    POP3服务器（端口995）	SMTP服务器（端口465或587）
    # qq.com	pop.qq.com	            smtp.qq.com
    mail_host = "smtp.qq.com"           # 设置服务器
    mail_port = "465"
    global receivers
    if receivers == []:
        print("收件人邮箱列表为空，检查脚本同文件夹下是否有{}以及里面是否有邮箱".format(mail_file))
        print("收件人邮箱列表为空，自动调整收件人为自己")
        receivers = [my_sender]
        log("收件人邮箱列表为空，检查脚本同文件夹下是否有{}以及里面是否有邮箱".format(mail_file))
        log("收件人邮箱列表为空，自动调整收件人为自己")
    print('收件人 {}'.format([receivers]))
    log('收件人 {}'.format(receivers))
    receiver_name = ""
    try:
        msg = MIMEMultipart()
        message = MIMEText(str(send_msg), 'plain', 'utf-8')              # 邮件内容
        msg['From'] = formataddr([send_name, my_sender])            # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        for receiver in receivers:
            msg['To'] = formataddr([receiver_name, receiver])        # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = send_subject                               # 邮件的主题，也可以说是标题
        msg.attach(message)
        # 添加附件
        for file in fujian_list:
            msg.attach(fu_jian(file))

        server = smtplib.SMTP_SSL(mail_host, mail_port)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, receivers, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        print("邮件发送成功")
        log("邮件发送成功")
    except smtplib.SMTPException as e:
        print("Error: 无法发送邮件")
        print(e)
        log("Error: 无法发送邮件")
        log(e)


def compare(file1, file2):
    f1_code_list = linecache.getlines(file1)
    f2_code_list = linecache.getlines(file2)
    if f1_code_list == []:
        if os.path.exists(file1):
            print("{} 内容为空".format(file1))
            log("{} 内容为空".format(file1))
        else:
            print("{} 不存在".format(file1))
            log("{} 不存在".format(file1))
        return []
    if f2_code_list == []:
        if os.path.exists(file2):
            print("{} 内容为空".format(file2))
            log("{} 内容为空".format(file2))
        else:
            print("{} 不存在".format(file2))
            log("{} 不存在".format(file2))
        return []
    if f1_code_list == f2_code_list:
        # 如果一样就是没变化不需要任何操作
        print('{} 和 {} 内容相同，不参与比较'.format(file1, file2))
        log('{} 和 {} 内容相同，不参与比较'.format(file1, file2))
        return []
    else:
        # 如果不一样找到不一样的地方
        if len(f1_code_list) == len(f2_code_list):
            line_remeber = []   # 记录不一样的行数
            # print(len(f2_code_list))
            for line in range(len(f2_code_list)):
                f1 = f1_code_list[line].strip()
                f2 = f2_code_list[line].strip()
                if f1 == f2:
                    pass
                else:
                    line_remeber.append(line)
            return line_remeber     # 返回不一样的行数
        else:
            print('{} 和 {} 行数不同，不参与比较'.format(file1, file2))
            log('{} 和 {} 行数不同，不参与比较'.format(file1, file2))
            return []


def compare_sendmail_loop():
    # 获取当前时间对象
    now = datetime.datetime.now()
    # 获取上一个小时的整点时间
    f1_name = (now + datetime.timedelta(hours=-1, minutes=-now.minute)).strftime("%Y-%m-%d+%H-%M")
    # 获取当前整点时间
    f2_name = (now + datetime.timedelta(hours=0, minutes=-now.minute)).strftime("%Y-%m-%d+%H-%M")
    f1_code_file = f1_name + 'code.txt'
    f2_code_file = f2_name + 'code.txt'
    f1_results_file = f1_name + 'urlresults.txt'
    f2_results_file = f2_name + 'urlresults.txt'
    compare_results = compare(f1_code_file, f2_code_file)     # 获取比较的结果
    send_msg = ""   # 邮件正文内容
    if compare_results:
        for line in compare_results:
            line = int(line) + 1
            url = linecache.getline(url_file, line).strip()
            f1_code = linecache.getline(f1_code_file, line).strip()
            f2_code = linecache.getline(f2_code_file, line).strip()
            send_msg = send_msg + url + "\t从 {} 变为 {} \n".format(f1_code, f2_code)
        send_msg = msg + send_msg
        file_list = [f1_code_file, f2_code_file, f1_results_file, f2_results_file]
        print(send_msg)
        log(send_msg)
        try:
            send_mail(send_name, send_subject, send_msg, file_list)
        except Exception as e:
            print('send_mail 失败')
            log('send_mail 失败')
            print(e)
            log(e)
    else:
        print('{} 和 {}两个文件内容行数不一样 或者 内容完全一样，这里不发送邮件'.format(f1_code_file, f2_code_file))
        log('{} 和 {}两个文件内容行数不一样 或者 内容完全一样，这里不发送邮件'.format(f1_code_file, f2_code_file))


if __name__ == '__main__':
    init()                  # 初始化
    makedir(results_dir)    # 创建结果文件夹,同时切换工作目录
    scheduler = BlockingScheduler()
    scheduler.add_job(url_test, 'cron', day_of_week='*', hour='*')
    scheduler.add_job(compare_sendmail_loop, 'cron', day_of_week='*', hour='*', minute='59')
    print(scheduler.get_jobs())
    scheduler.start()
    # 主要测试：
    # compare_sendmail_loop()
