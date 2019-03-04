# 使用SSH下载服务器文件

瞎xx写 BY: zzy0302
## 测试环境:
Windows 10 1809 with python 3.7.1

## 使用说明：

	pip install -r requirements.txt
	python download.py {username} {password} {order}

username: 登录服务器用的用户名

password：登录服务员用的密码

order：

- s --扫描服务器文件，并保存到文件./filelist/10.60.41.1.txt
- d --下载扫描的文件，必须先扫描再下载，并保存到文件./download