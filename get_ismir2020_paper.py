
import urllib.request
from urllib.request import urlretrieve
import time
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

basic_url = 'https://program.ismir2020.net/static/final_papers/'
opener = urllib.request.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/49.0.2')]
n = 0
count = 0
print('开始检查：')
while n<800:
	tempUrl = basic_url + '%d.pdf'%n
	try :
		opener.open(tempUrl)
		print('%06d.pdf'%n+' 没问题')
		print("start downloading")
		urlretrieve(tempUrl, 'ismir2020/' + '%06d.pdf'%n)
		count += 1
	except urllib.error.HTTPError:
		print('%06d.pdf'%n+' 访问页面出错')
		time.sleep(2)
	except urllib.error.URLError:
		print('%06d.pdf'%n+' 访问页面出错')
		time.sleep(2)
	time.sleep(0.1)
	n += 1
print("Available papers: ", count)

