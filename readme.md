# 树莓派开机自动发送局域网ip和cpolar的隧道信息到指定邮箱

***

### 一直想找能够开机发送cpolar的隧道的代码，但是貌似发现有没有人有这个需求，本代码在已有代码基础上增加了这个功能。
### [cpolar](https://www.cpolar.com/)是内网穿透工具，非常好用，推荐！！
下面内容包括三个部分：
1. 运行步骤
2. 如何如何获取cpolar的cookies
3. 如何获取SMTP

***

## 运行步骤
1. 复制mail.py到您的派派上并进行相关信息修改。
2. 修改/ect/rc.local信息，添加python /home/pi/mail.py >> /home/pi/mail.log 2>&1在exit0之前，注意文件的绝对路径位置。
``` sh
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi
python /home/pi/mail.py >> /home/pi/mail.log 2>&1 #注意要修改为文件的绝对路径
exit 0
```
---
## 如何获取cpolar的cookies
1. 在登录cpolar之前先开启开发人员工具(360浏览器右键的审查元素)，点击网络，然后登进去你的账号并进入仪表盘。此时开发工具的网络部分会有内容，status中就藏有cookies。
![](/cookies1.png)
2. 点击status，右边找到cookies即可，cookies:右边的就是我们的cookies。
![](/cookies2.png)
## 如何获取SMTP 
1. QQ邮箱中点击设置-账户，然后开启smtp并且生成您的授权码。
![](/smtp.png)

