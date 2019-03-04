import os
import sys
import time
import queue
import random
import paramiko
import threading

class SSHConnection(object):
	def __init__(self, host = '10.60.41.1', port = 22, username = '',pwd = '1234'):
		# print(self.object)
		self.host = host
		self.port = port
		self.username = username
		self.pwd = pwd
		self.__k = None

	def connect(self):
		transport = paramiko.Transport((self.host, self.port))
		transport.connect(username = self.username, password = self.pwd)
		self.__transport = transport
		if(len(transport.get_username()) > 0):
			print('[SSH]:以用户 ' + transport.get_username() + ' 身份登陆')
			return True
		return False

	def close(self):
		self.__transport.close()

	def upload(self,local_path,target_path):
		sftp = paramiko.SFTPClient.from_transport(self.__transport)
		sftp.put(local_path, target_path)

	def download(self,remote_path,local_path):
		sftp = paramiko.SFTPClient.from_transport(self.__transport)
		sftp.get(remote_path,local_path)

	def cmd(self, command):
		ssh = paramiko.SSHClient()
		ssh._transport = self.__transport
		stdin, stdout, stderr = ssh.exec_command(command)
		return stdout.read()

def mkdir(pathf):
	global local_path
	path = local_path + '/'.join(pathf[37:].split('/')[:-1])
	if not os.path.exists(path):
		os.makedirs(path) 

def searchfile(pwd,startlist,thread_filename):
	if pwd[-1] != '/':
		pwd += '/'
	global floderqueue,current_filecount,flodernamecount,current_filelist,filequeue
	for i in startlist:
		if len(i) > 0 :
			temp = list(filter(None,i.split(' ')))
			if i[0] == 'd' and '$' not in i and 'CICS' not in i:
				floderqueue.put(pwd + ' '.join(temp[8:]))
				flodernamecount += 1
			elif i[0] == '-' and '$' not in i and 'CICS' not in i:
				current_filecount += 1
				thread_filename.write(pwd + ' '.join(temp[8:]) + '\n')
				filequeue.put(pwd + ' '.join(temp[8:]))

def scan_queue():
	time_start = time.time()
	global floderqueue,current_filelist,count,wtf
	while not floderqueue.empty():
		temp = floderqueue.get()
		if temp == wtf:
			print(temp)
		else:
			floderqueue.put(temp)
			wtf = temp
		print('[QUEUE]:DFS队列剩余任务数: ' + str(floderqueue.qsize()) + ', 已用时间: ' + str(time.time() - time_start).split('.')[0] + 'S, 已发现文件数: ' + str(current_filecount) + ', 已发现文件夹数: ' + str(flodernamecount))
		time.sleep(random.randint(2,5))

def get_filelist(thread_number):
	global floderqueue,ls_lop,ssh
	with open('./filelist/10.60.41.1-' + str(thread_number) + '.txt','w') as new_file:
		try:
			while not floderqueue.empty():
				tempname = floderqueue.get()
				templist = ssh.cmd(ls_lop + tempname).decode().split('\n')[1:-1]
				searchfile(tempname,templist,new_file)
				# floderqueue.task_done()
			print('[SYSTEM]:线程 ' + str(thread_number) + '保存文件成功')
		except Exception:
			pass

def download(i):
	global filequeue
	print('剩余文件: '+str(filequeue.qsize())+'正在下载: ' + i[37:].split('/')[-1])
	try:
		mkdir(i)
		ssh.download(i,'I:\\download\\download' + i[37:])
	except Exception:
		pass

def download_file():
	time.sleep(5)
	global filequeue
	print('[SYSTEM]:准备下载文件')
	while not filequeue.empty():
		i = filequeue.get()
		download_thread = threading.Thread(target = download,args = [i])
		download_thread.start()
		time.sleep(0.4)

if __name__ == "__main__":
	if len(sys.argv) >= 3:
		username=sys.argv[1]
		password=sys.argv[2]
		operate=sys.argv[3:]
	else:
		print('[SYSTEM]:缺少必要参数，请补全用户名与密码')
	wtf = None
	ssh = SSHConnection(username = username,pwd = password)
	floderqueue = queue.LifoQueue()
	filequeue = queue.LifoQueue()
	ls_lop = 'ls -l '
	lsop = 'ls '
	flodernamecount = 0
	start_path = 'data/publicfiles/CourseDocuments_课程文档/'
	local_path = './download'
	current_filecount = 0
	current_filelist = []
	double_list = []
	old_filelist = []
	get_file_threads = []
	try:
		with open('./filelist/10.60.41.1.txt','r') as old_file:
			temp = old_file.read().split('\n')
			for i in temp:
				old_filelist.append(i)
	except Exception:
		pass
	print('[SYSTEM]:初始化完成')
	if(ssh.connect()):
		print('[SSH]:连接成功')
	else:
		print('[SSH]:连接失败,请检查网络环境及账户密码')
		exit()

	if 's' in operate: 
		filelist = ssh.cmd(lsop + start_path).decode().split('\n')
		startlist = ssh.cmd(ls_lop + start_path + filelist[-1]).decode().split('\n')[1:]
		with open('./filelist/10.60.41.1.txt','w') as new_file:
			searchfile(start_path + filelist[-1],startlist,new_file)
		print('[QUEUE]:初始化队列完成')
		print('[SYSTEM]:开始工作')
		scan = threading.Thread(target = scan_queue)
		scan.start()
		for i in range (8):
			tempthread = threading.Thread(target = get_filelist,args = [i])
			get_file_threads.append(tempthread)
		for i in get_file_threads:
			i.start()
		print('[SYSTEM]:准备下载文件')
		downthread=threading.Thread(target=download_file)
		downthread.start()
		threading.Thread.join(downthread)
		for i in get_file_threads:
			threading.Thread.join(i)
		while not floderqueue.empty():
			time.sleep(1)
		print('[SYSTEM]:共 ' + str(current_filecount) + ' 个文件')
		print('[SYSTEM]:共 ' + str(flodernamecount) + ' 个文件夹')

	if 'd' in operate: 
		print('[SYSTEM]:准备下载文件')
		downthread=threading.Thread(target=download_file)
		downthread.start()
		threading.Thread.join(downthread)
	if 's' in operate: 
		print('[SYSTEM]:准备合并文件')
		filepwd=os.getcwd()+'./filelist'
		filenames=os.listdir(filepwd)
		with open('./filelist/10.60.41.1.txt','w') as all_file_list:
			for filename in filenames:
				if '-' in filename:
					print('[SYSTEM]:文件: ' + filename + ' 正在合并···')
					with open('./filelist/' + filename,"r") as infile:
						for i in infile:
							all_file_list.write(i)
					os.remove(filepwd + '/' + filename)
					print('[SYSTEM]:文件: ' + filename + ' 已合并')
		print('[SYSTEM]:合并文件完成')

ssh.close()
print('[SSH]:连接关闭')
