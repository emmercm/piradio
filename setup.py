#!/usr/bin/env python

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
	print "PiRadio setup requires root priveleges."
	sys.exit(1)
	
	
# Check for i2c_dev module in startup
modules = subprocess.check_output("cat /proc/modules", shell=True)
if not "i2c_dev" in modules:
	with open('/etc/modules', 'r+') as f:
		if not "i2c-dev" in f.read():
			print "I2C module is not loaded and is not in /etc/modules, adding..."
			f.write("i2c-dev\n")
			print "Reboot recommended."
	
	
# Import/install+import APT
try:
	import apt
except ImportError:
	print "Installing python-apt..."
	os.system("sudo apt-get install python-apt")
	try:
		import apt
	except ImportError:
		print "python-apt install fail"
		sys.exit(1)
	else:
		print "python-apt install success"
	print ""

# Prep APT cache for usage
sys.stdout.write("Getting APT cache... ")
sys.stdout.flush()
apt_cache = apt.cache.Cache()
apt_cache.update()
apt_cache.open(None) # re-read package list
sys.stdout.write("done\n\n")
sys.stdout.flush()

# Install missing APT packages
apt_commit = False
for package_name in ["python-dev","python-smbus","vlc"]:
	apt_package = apt_cache[package_name]
	if not apt_package.is_installed:
		print "Marking "+package_name+" for install"
		apt_package.mark_install()
		apt_commit = True
if apt_commit:
	try:
		apt_cache.commit(install_progress=None)
	except Exception, arg:
		print "APT install fail"
	else:
		print "APT install success"
	print ""
	
	
# Install pip if missing
if which("pip") == False:
	print "Downloading pip installer..."
	if os.path.isfile("get-pip.py"):
		os.remove("get-pip.py")
	urllib.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
	if not os.path.isfile("get-pip.py"):
		print "Download fail"
	else:
		print "Download success"
		print "Installing pip..."
		os.system("sudo python get-pip.py")
		if os.path.isfile("get-pip.py"):
			os.remove("get-pip.py")
		if which("pip") == False:
			print "pip install fail"
		else:
			print "pip install success"
	print ""
	
	
# Installing missing pip packages
if which("pip") == True:
	# Old versions of pip don't have "list" command, upgrade pip first
	print "Upgrading pip..."
	os.system("sudo pip install --upgrade pip")
	
	pip_list = subprocess.check_output("pip list", shell=True)
	for package_name in ["natsort","cherrypy","formencode","genshi","dot3k"]:
		found = False
		for line in pip_list.splitlines():
			if line.split(" ")[0].lower() == package_name.lower():
				found = True
				break
		if found == False:
			print "Installing "+package_name+"..."
			os.system("sudo pip install "+package_name)
		else:
			print "Upgrading "+package_name+"..."
			os.system("sudo pip install --upgrade "+package_name)
	print ""