#!/usr/bin/env python

import __builtin__
import atexit
import os
import sys
import threading
import time
import urllib2

import Player
import WebServer

__builtin__.OutputDisplay = None
__builtin__.PlaybackModule = None
__builtin__.CherryServer = None

__builtin__.Shutdown = threading.Event()

__builtin__.Status = {}


# Thread to keep track of global status
class UpdateStatus(threading.Thread):
	def InternetConnected(self):
		try:
			urllib2.urlopen('http://74.125.228.100', timeout=1)
			return True
		except urllib2.URLError:
			return False
	def run(self):
		timer_internet = 0
		while not __builtin__.Shutdown.isSet():
			# 'Playing'
			if __builtin__.PlaybackModule != None:
				__builtin__.Status['Playing'] = __builtin__.PlaybackModule.IsPlaying()
			else:
				__builtin__.Status['Playing'] = False
			# 'Internet'
			if timer_internet == 0 or (timer_internet + 10) <= time.time():
				__builtin__.Status['Internet'] = self.InternetConnected()
				timer_internet = time.time()
			# 'TrackInfo'
			if __builtin__.PlaybackModule != None:
				__builtin__.Status['TrackInfo'] = __builtin__.PlaybackModule.GetInfo()
			else:
				__builtin__.Status['TrackInfo'] = {}
			time.sleep(0.05)
			
			
@atexit.register
def onexit():
	__builtin__.Shutdown.set()
	if __builtin__.PlaybackModule != None:
		__builtin__.PlaybackModule.Stop()
	if __builtin__.CherryServer != None:
		__builtin__.CherryServer.stop()
		__builtin__.CherryServer.join()


if __name__ == '__main__':
	# Start UpdateStatus() thread
	status = UpdateStatus()
	status.start()
	
	# Start CherryPy thread
	__builtin__.CherryServer = WebServer.WebServer.Server()
	__builtin__.CherryServer.start()
	
	# CHANGE
	__builtin__.OutputDisplay = Player.OutputDisplays.DisplayOTron3k()
	
	# DEBUG
	__builtin__.PlaybackModule = Player.PlaybackModules.VLCPlayback()
	
	# Display PlaybackModules menu (main loop that does not exit)
	if __builtin__.OutputDisplay != None:
		modules_menu = {}
		for module in Player.PlaybackModules.PlaybackModule.__subclasses__():
			modules_menu = dict(modules_menu.items() + module.Menu.items())
		__builtin__.OutputDisplay.DisplayMenu(modules_menu)
	
	# Clean exit
	exit(0)