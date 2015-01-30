import os
import sys


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
apt_cache = apt.cache.Cache()
apt_cache.update()
# Install missing APT packages
apt_commit = False
for package_name in ["vlc"]:
	apt_package = apt_cache[package_name]
	if not apt_package.is_installed:
		sys.stdout.write("Marking "+package_name+" for install\n")
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