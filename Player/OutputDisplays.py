import __builtin__
import abc
import math
import os
import subprocess
import sys
import threading
import time


"""
This is the Menu class to hold information about menus such as items and current position.
"""

class Menu(object):
	def __init__(self, menu, *args):
		self.Menu = menu
		self.Paused = False
		self._line = 0
		
	def line_get(self):
		return self._line
	def line_set(self, value):
		if value < 0:
			value = 0
		if value >= len(self.Menu):
			value = len(self.Menu) - 1
		self._line = value
	line = property(line_get, line_set)
		
	def GetLines(self, lines):
		# Calculate line_start
		line_start = self.line - int(math.floor(lines/2))
		if line_start < 0: line_start = 0
		# Calculate line_end
		line_end = line_start + lines
		if line_end > len(self.Menu):
			line_end = len(self.Menu)
			line_start = line_end - lines
			if line_start < 0: line_start = 0
		
		items = sorted(self.Menu.keys(),key=str.lower)
		for i, item in enumerate(items):
			if i == self.line:
				items[i] = '> ' + items[i]
			else:
				items[i] = '  ' + items[i]
		return items[line_start:line_end]
		
	def GetText(self):
		return sorted(self.Menu.keys(),key=str.lower)[self.line]
	def GetValue(self):
		return self.Menu[sorted(self.Menu.keys(),key=str.lower)[self.line]]
		
		
"""
This is the abstract class for all OutputDisplays.
All OutputDisplays need to implement the @abstractmethods in order to function.
"""

class OutputDisplay(object):
	__metaclass__ = abc.ABCMeta
	
	def __init__(self, *args):
		self.Clear()
		self.display_height = 0
		self.display_width = 0
		self.menus = []
		self.events = {}
		self.last_event = time.time()
		
		
	def MenuOpen(self, menu, start=0):
		menu_obj = Menu(menu)
		menu_obj.line = start
		self.menus.append(menu_obj)
		self.MenuPrint()
		
	def MenuCurr(self):
		if len(self.menus) == 0:
			return None
		return self.menus[len(self.menus)-1]
		
	def MenuPrint(self):
		self.Clear()
		if self.MenuCurr() != None:
			menu_lines = self.MenuCurr().GetLines(self.display_height)
			for i, line in enumerate(menu_lines):
				self.PrintLine(i, line)
				
	def HandleUp(self):
		self.events['ButtonUp'] = True
		if self.MenuCurr().Paused == False:
			self.MenuCurr().line -= 1
			self.MenuPrint()
		self.last_event = time.time()
	def HandleDown(self):
		self.events['ButtonDown'] = True
		if self.MenuCurr().Paused == False:
			self.MenuCurr().line += 1
			self.MenuPrint()
		self.last_event = time.time()
		
	def HandleForward(self):
		self.events['ButtonForward'] = True
		self.last_event = time.time()
	def HandleBack(self):
		self.events['ButtonBack'] = True
		self.last_event = time.time()
	def HandleSelect(self):
		self.events['ButtonSelect'] = True
		self.last_event = time.time()
		
	def DisplayMenu(self, menu, start=0):
		self.MenuOpen(menu, start)
		menu_depth = len(self.menus)
		
		# Wait on events
		while len(self.menus) != (menu_depth-1):
			
			if 'ButtonSelect' in self.events or 'ButtonForward' in self.events:
				self.events.pop('ButtonSelect',None)
				self.events.pop('ButtonForward',None)
				item = self.MenuCurr().GetValue()
				if type(item) is dict:
					# CME TODO: Nested menus
					pass
				else:
					self.MenuCurr().Paused = True
					if item(self.MenuCurr().GetText()) == 1:
						self.HandleBack() # function indicated menu should close
					else:
						self.events = {} # ignore any lingering events
						self.MenuPrint() # redraw just in case
					self.MenuCurr().Paused = False
				
			if 'ButtonBack' in self.events:
				self.events.pop('ButtonBack',None)
				self.menus.pop()
				self.MenuPrint()
				
			if (self.last_event + 5) <= time.time() and __builtin__.PlaybackModule.IsLoaded():
				self.DisplayTrack()
				self.MenuPrint()
				
			time.sleep(0.05)
			
		self.events = {}
		return 1
		
		
	def DisplayTrack(self):
		self.Clear()
		self.events = {}
		
		status_curr = None
		while True:
			if 'ButtonSelect' in self.events:
				self.events.pop('ButtonSelect',None)
				__builtin__.PlaybackModule.Toggle()
			if 'ButtonUp' in self.events:
				self.events.pop('ButtonUp',None)
				__builtin__.PlaybackModule.Prev()
			if 'ButtonDown' in self.events:
				self.events.pop('ButtonDown',None)
				__builtin__.PlaybackModule.Next()
				
			if 'ButtonBack' in self.events:
				self.events.pop('ButtonBack',None)
				break
			
			# Output track info
			status_new = __builtin__.Status['TrackInfo']
			if status_new != status_curr:
				if self.display_height == 3:
					self.PrintLine(0, status_new['artist'])
					self.PrintLine(1, status_new['title'])
					
				out_time = '>' if __builtin__.PlaybackModule.IsPlaying() else '#'
				out_time += ' ' + self.FormatTime(status_new['elapsed'])
				if status_new['length'] > 0:
					out_time += ' / ' + self.FormatTime(status_new['length'])
				self.PrintLine(self.display_height-1, out_time)
				
				status_curr = status_new
				
			time.sleep(0.01)
			
		self.events = {}
		return 0
		
	def FormatTime(self, sec):
		if sec < 0: sec = 0
		out = ""
		if sec >= 3600: # >=1 hour
			out += str(sec/3600)
			out += str(sec/60).zfill(2)
		else: # <1 hour
			out += str(sec/60)
		out += ":" + str(sec%60).zfill(2)
		return out
		
		
	@abc.abstractmethod
	def Clear(self):
		return
		
	@abc.abstractmethod
	def PrintLine(self, line, str):
		return
		
		
"""
This is the OutputDisplay module for Pimoroni's Display-O-Tron 3000 LCD.
Known issue: something in dot3k library causes sys.exit() to hang
"""

# Some WARNs for dot3k imports
# Check root requirement
if os.geteuid() != 0:
	sys.stdout.write("WARN: Display-O-Tron 3000 LCD display requires root priveleges for /dev/mem.\n")
# Check module requirements
modules = subprocess.check_output("cat /proc/modules", shell=True)
if not "spi_bcm2708" in modules:
	sys.stdout.write("WARN: Display-O-Tron 3000 LCD display requires SPI to be enabled.\n")
if not "i2c_bcm2708" in modules:
	sys.stdout.write("WARN: Display-O-Tron 3000 LCD display requires I2C to be enabled.\n")
if not "i2c_dev" in modules:
	sys.stdout.write("WARN: Display-O-Tron 3000 LCD display requires I2C-Dev to be enabled.\n")
import dot3k.backlight
import dot3k.joystick
import dot3k.lcd

class DisplayOTron3k(OutputDisplay):
	def __init__(self, *args):
		super(DisplayOTron3k, self).__init__(*args)
		self.display_height = 3
		self.display_width = 16
		
		dot3k.backlight.rgb(150,150,150)
		
		# Handle up button
		@dot3k.joystick.on(dot3k.joystick.UP)
		def handle_up(pin):
			self.HandleUp()
			dot3k.joystick.repeat(dot3k.joystick.UP, self.HandleUp, 0.5, 1.5)
		# Handle down button
		@dot3k.joystick.on(dot3k.joystick.DOWN)
		def handle_down(pin):
			self.HandleDown()
			dot3k.joystick.repeat(dot3k.joystick.DOWN, self.HandleDown, 0.5, 1.5)
		# Handle left button
		@dot3k.joystick.on(dot3k.joystick.LEFT)
		def handle_left(pin):
			self.HandleBack()
			# dot3k.joystick.repeat(dot3k.joystick.LEFT, self.HandleBack, 0.5, 1.5)
		# Handle right button
		@dot3k.joystick.on(dot3k.joystick.RIGHT)
		def handle_right(pin):
			self.HandleForward()
			# dot3k.joystick.repeat(dot3k.joystick.RIGHT, self.HandleForward, 0.5, 1.5)
		# Handle select button
		@dot3k.joystick.on(dot3k.joystick.BUTTON)
		def handle_button(pin):
			self.HandleSelect()
			# dot3k.joystick.repeat(dot3k.joystick.BUTTON, self.HandleSelect, 0.5, 1.5)
			
		# Jukebox-like color effect for the screen
		class Jukebox(threading.Thread):
			def run(self):
				hue = 0.0
				while not __builtin__.Shutdown.isSet():
					hue += 0.002
					if hue > 1.0: hue -= 1.0
					dot3k.backlight.sweep(hue)
					time.sleep(0.01)
		jukebox = Jukebox()
		jukebox.start()
		
	def Clear(self):
		dot3k.lcd.clear()
		
	def PrintLine(self, line, str):
		dot3k.lcd.set_cursor_position(0, line)
		dot3k.lcd.write(str[:self.display_width].ljust(self.display_width))
		return