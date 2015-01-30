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
	
	
# Import APT
try:
	import apt
except ImportError:
	sys.stdout.write("\nPiRadio setup requires python-apt to be installed.\n")
	sys.exit(1)

# Prep APT cache for usage
sys.stdout.write("Getting APT cache... ")
sys.stdout.flush()
apt_cache = apt.cache.Cache()
apt_cache.update()
sys.stdout.write("done\n")
sys.stdout.flush()

# Install missing APT packages
apt_commit = False
for package_name in ["python-dev","vlc"]:
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
	os.remove("get-pip.py")
	urllib.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
	if not os.path.isfile("get-pip.py"):
		sys.stdout.write("fail\n")
	else:
		sys.stdout.write("success\n")
		sys.stdout.write("Installing pip...\n")
		sys.stdout.flush()
		os.system("sudo python get-pip.py")
		os.remove("get-pip.py")
		if which("pip") == False:
			sys.stdout.write("pip install fail\n")
		else:
			sys.stdout.write("pip install success\n")
	sys.stdout.write("\n")
	sys.stdout.flush()
	
	
# Installing missing pip packages
if which("pip") == True:
	pip_installed = False
	pip_list = subprocess.check_output("pip list", shell=True)
	for package_name in ["cherrypy","genshi"]:
		found = False
		for line in pip_list.splitlines():
			if line.split(" ")[0].lower() == package_name.lower():
				found = True
				break
		if found == False:
			sys.stdout.write("Installing "+package_name+"...\n")
			sys.stdout.flush()
			os.system("sudo pip install "+package_name)
			pip_installed = True
	if pip_installed == True:
		sys.stdout.write("\n")
		sys.stdout.flush()