#!/usr/bin/python
# -*- coding: UTF-8 -*-
import time
import smtplib
import urllib
import urllib.request
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

import requests
from lxml import etree
from bs4 import BeautifulSoup

my_sender = '**********@qq.com'  # 发件人QQ邮箱账号
my_pass = '**********'  # 发件SMTP授权码
my_user = '**********'  # 收件人QQ邮箱账号，自己发自己就行
cookie = '''填写你登录cpoolar的cookies'''

def cpolar():
    header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
    'Connection': 'keep-alive',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cookie': cookie}
    url = 'https://dashboard.cpolar.com/status'
    html = requests.get(url,headers=header).text
    e = etree.HTML(html)
    #xpath解析语法，cpolar默认是三个隧道信息，本来我只想要ssh这个，但是后来测试发现三个隧道的html中位置有时候会随机变换，索性全部隧道信息都添加上。
    names = e.xpath('/html/body/div[5]/div/div[2]/div[2]/table/tbody/tr[1]/th/a/text()')
    names.append(e.xpath('/html/body/div[5]/div/div[2]/div[2]/table/tbody/tr[2]/th/a/text()'))
    names.append(e.xpath('/html/body/div[5]/div/div[2]/div[2]/table/tbody/tr[3]/th/a/text()'))
    if(len(names) != 3):
        alltunnel = '您的cookies过期了'
    else: alltunnel = str(names[0]) + "  "+ str(names[1][0]) + "  "+ str(names[2][0])  
    return alltunnel


def mail():
    ret = True
    try:
       # msg = MIMEText('填写邮件内容', 'plain', 'utf-8')
        msg = MIMEMultipart()
        msg['From'] = formataddr(["树莓派", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = formataddr(["树莓派", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = "树莓派IP地址"  # 邮件的主题，也可以说是标题
 
        # 邮件正文内容
        msg.attach(MIMEText("局域网ip："+ip+"\n cpolar：\n"+ alltunnel, 'plain', 'utf-8'))
 
        server = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
    return ret
 
# 检查网络连同性
def check_network():
    while True:
        try:
            result=urllib.request.urlopen('https://www.baidu.com').read()
            print(result)
            print("Network is Ready!")
            break
        except Exception:
           print(err)
           print("Network is not ready,Sleep 5s....")
           time.sleep(5)
    return True
 
# 获得本级制定接口的ip地址
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1",80))
    ipaddr=s.getsockname()[0]
    s.close()
    return ipaddr
    
if __name__=='__main__':
    time.sleep(15)
    check_network()
    ip=get_ip_address()
    alltunnel = cpolar()
    ret = mail()
    if ret:
        print("OK")
    else:
        print("error")
