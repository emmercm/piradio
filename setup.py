import os
import urllib
import subprocess
import sys


def which(bin):
	found = False
	for path in os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		if os.path.isfile( os.path.join(path, bin) ):
			found = True
			break
	return found


if os.geteuid() != 0:
	sys.stdout.write("PiRadio setup requires root priveleges.\n")
	sys.exit(1)
	
	
# Check for i2c_dev module in startup
modules = subprocess.check_output("cat /proc/modules", shell=True)
if not "i2c_dev" in modules:
	with open('/etc/modules', 'r+') as f:
		if not "i2c-dev" in f.read():
			sys.stdout.write("I2C module is not loaded and is not in /etc/modules, adding...\n")
			sys.stdout.flush()
			f.write("i2c-dev\n")
			sys.stdout.write("Reboot recommended.\n")
			sys.stdout.flush()
	
	
# Import/install+import APT
try:
	import apt
except ImportError:
	sys.stdout.write("Installing python-apt...\n")
	sys.stdout.flush()
	os.system("sudo apt-get install python-apt")
	try:
		import apt
	except ImportError:
		sys.stdout.write("python-apt install fail\n")
		sys.stdout.flush()
		sys.exit(1)
	else:
		sys.stdout.write("python-apt install success\n")
	sys.stdout.write("\n")
	sys.stdout.flush()

# Prep APT cache for usage
sys.stdout.write("Getting APT cache... ")
sys.stdout.flush()
apt_cache = apt.cache.Cache()
apt_cache.update()
sys.stdout.write("done\n\n")
sys.stdout.flush()

# Install missing APT packages
apt_commit = False
for package_name in ["python-dev","python-smbus","vlc"]:
	apt_package = apt_cache[package_name]
	if not apt_package.is_installed:
		sys.stdout.write("Marking "+package_name+" for install\n")
		sys.stdout.flush()
		apt_package.mark_install()
		apt_commit = True
if apt_commit:
	try:
		apt_cache.commit(install_progress=None)
	except Exception, arg:
		sys.stdout.write("APT install fail\n")
	else:
		sys.stdout.write("APT install success\n")
	sys.stdout.write("\n")
	sys.stdout.flush()
	
	
# Install pip if missing
if which("pip") == False:
	sys.stdout.write("Downloading pip installer... ")
	sys.stdout.flush()
	if os.path.isfile("get-pip.py"):
		os.remove("get-pip.py")
	urllib.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
	if not os.path.isfile("get-pip.py"):
		sys.stdout.write("fail\n")
	else:
		sys.stdout.write("success\n")
		sys.stdout.write("Installing pip...\n")
		sys.stdout.flush()
		os.system("sudo python get-pip.py")
		if os.path.isfile("get-pip.py"):
			os.remove("get-pip.py")
		if which("pip") == False:
			sys.stdout.write("pip install fail\n")
		else:
			sys.stdout.write("pip install success\n")
	sys.stdout.write("\n")
	sys.stdout.flush()
	
	
# Installing missing pip packages
if which("pip") == True:
	pip_list = subprocess.check_output("pip list", shell=True)
	for package_name in ["cherrypy","formencode","genshi","dot3k"]:
		found = False
		for line in pip_list.splitlines():
			if line.split(" ")[0].lower() == package_name.lower():
				found = True
				break
		if found == False:
			sys.stdout.write("Installing "+package_name+"...\n")
			sys.stdout.flush()
			os.system("sudo pip install "+package_name)
		else:
			sys.stdout.write("Upgrading "+package_name+"...\n")
			sys.stdout.flush()
			os.system("sudo pip install --upgrade "+package_name)
	sys.stdout.write("\n")
	sys.stdout.flush()