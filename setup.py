#!/usr/bin/env python

import os
import urllib
import shutil
import subprocess
import sys
import tempfile


def which(bin):
	for path in os.environ["PATH"].split(os.pathsep):
		path = path.strip('"')
		if os.path.isfile( os.path.join(path, bin) ):
			return True
	return False


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
	
	
# Add mopidy GPG apt-key
apt_key_list = subprocess.check_output("sudo apt-key list", shell=True)
if not "271D2943" in apt_key_list:
	print "Adding apt.mopidy.com GPG key to apt-get..."
	os.system("wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -")
	apt_key_list = subprocess.check_output("sudo apt-key list", shell=True)
	if not "271D2943" in apt_key_list:
		print "GPG key add fail"
	else:
		print "GPG key add success"
# Add mopidy to APT source list
if not os.path.isfile("/etc/apt/sources.list.d/mopidy.list"):
	print "Adding apt.mopidy.com to APT source list..."
	os.system("sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/mopidy.list")
	if not os.path.isfile("/etc/apt/sources.list.d/mopidy.list"):
		print "Download fail"
	else:
		print "Running apt-get update..."
		os.system("sudo apt-get update")

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
for package_name in [
"python-dev","python-smbus","build-essential", # I2C/SPI
"vlc", # VLC
"libgnutls-dev","libjson0-dev","libavcodec-dev","libavformat-dev","libavfilter-dev","libao-dev", # pianobar
"libspotify-dev","libffi-dev","libasound2-dev","python-alsaaudio" # Spotify
]:
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
	
	
# Install/upgrade pip packages
if which("pip") == True:
	# Old versions of pip don't have "list" command, upgrade pip first
	print "Upgrading pip..."
	os.system("sudo pip install --upgrade pip")
	
	pip_list = subprocess.check_output("pip list", shell=True)
	for package_name in [
	"natsort",
	"cherrypy","formencode","genshi", # web server
	"dot3k", # Pimoroni Display-O-Tron 3000
	"pexpect", # python-pianobar
	"--pre pyspotify" # Spotify
	]:
		found = False
		for line in pip_list.splitlines():
			if line.split(" ")[0].lower() == package_name.split(" ")[-1].lower():
				found = True
				break
		if found == False:
			print "Installing "+package_name+"..."
			os.system("sudo pip install "+package_name)
		else:
			print "Upgrading "+package_name+"..."
			os.system("sudo pip install --upgrade "+package_name)
	print ""
	
	
# Install pianobar (Pandora)
# Requires: "libgnutls-dev", "libjson0-dev", "libavcodec-dev", "libavformat-dev", "libavfilter-dev", "libao-dev"
if which("pianobar") == False:
	print "Cloning pianobar from git..."
	temp_pianobar = tempfile.mkdtemp()
	if os.path.isdir(temp_pianobar):
		os.system("git clone --depth 1 https://github.com/PromyLOPh/pianobar.git "+temp_pianobar)
		if os.path.isfile(os.path.join(temp_pianobar, 'Makefile')):
			print "Running make install..."
			os.system("make --directory "+temp_pianobar)
			os.system("make --directory "+temp_pianobar+" install") # needs root
			shutil.rmtree(temp_pianobar)
			if which("pianobar") == True:
				print "Pianobar install success"
			else:
				print "Pianobar install failed"
		else:
			print "Git clone failed"
	else:
		print "Temporary directory creation failed"
	print ""