import __builtin__
import abc
import copy
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
	def __init__(self, menu, lines, *args):
		self._menu = menu
		self.Paused = False
		self._line = 0
		self._lines = lines
		
	def line_get(self):
		return self._line
	def line_set(self, value):
		if value < 0:
			value = 0
		if value >= len(self._menu):
			value = len(self._menu) - 1
		self._line = value
	line = property(line_get, line_set)
	
	def MenuKeys(self):
		items = copy.copy(self._menu)
		for idx, item in enumerate(items):
			items[idx] = item[0]
		return items
		
	def GetItem(self):
		return self._menu[self.line]
		
	def CalcLineStartEnd(self):
		# Calculate line_start
		line_start = self.line - int(math.floor(self._lines/2))
		if line_start < 0: line_start = 0
		# Calculate line_end, adjust line_start
		line_end = line_start + self._lines
		if line_end > len(self._menu):
			line_end = len(self._menu)
			line_start = line_end - self._lines
			if line_start < 0: line_start = 0
		return line_start, line_end
	def CalcLineCurr(self):
		line_start, line_end = self.CalcLineStartEnd()
		return self.line - line_start
		
	def GetLines(self, offset=0):
		line_start, line_end = self.CalcLineStartEnd()
		items = self.MenuKeys()
		for idx, item in enumerate(items):
			if idx == self.line:
				items[idx] = '> ' + (items[idx])[offset:]
			else:
				items[idx] = '  ' + items[idx]
		return items[line_start:line_end]
		
		
"""
This is the abstract class for all OutputDisplays.
All OutputDisplays need to implement the @abstractmethods in order to function.
"""

class OutputDisplay(object):
	__metaclass__ = abc.ABCMeta
	
	def __init__(self, *args):
		self.Clear()
		self.printing = False
		self.display_height = 0
		self.display_width = 0
		self.display_offset = 0
		self.display_offset_timer = 0
		self.menus = []
		self.events = {}
		self.last_event = time.time()
		
		
	def MenuOpen(self, menu, start=0):
		menu_obj = Menu(menu, self.display_height)
		menu_obj.line = start
		self.menus.append(menu_obj)
		self.MenuPrint()
		
	def MenuCurr(self):
		if len(self.menus) == 0:
			return None
		return self.menus[len(self.menus)-1]
		
	def MenuPrint(self, line_num=None):
		while self.printing: # allow only one MenuPrint() at once
			time.sleep(0.05)
		self.printing = True
		if not line_num is None:
			if line_num < 0 or line_num > self.display_height:
				line_num = None
		if line_num is None:
			self.Clear()
		if self.MenuCurr() != None:
			menu_lines = self.MenuCurr().GetLines(self.display_offset)
			for idx, line in enumerate(menu_lines):
				if line_num is None or idx == line_num:
					self.PrintLine(idx, line)
		self.printing = False
		
	def HandleUp(self):
		self.events['ButtonUp'] = True
		if self.MenuCurr().Paused == False:
			self.MenuCurr().line -= 1
			self.display_offset = 0
			self.display_offset_timer = time.time()
			self.MenuPrint()
		self.last_event = time.time()
	def HandleDown(self):
		self.events['ButtonDown'] = True
		if self.MenuCurr().Paused == False:
			self.MenuCurr().line += 1
			self.display_offset = 0
			self.display_offset_timer = time.time()
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
		self.display_offset = 0 # needs to happen before MenuOpen()
		self.display_offset_timer = time.time()
		self.MenuOpen(menu, start)
		menu_depth = len(self.menus)
		
		# Wait on events
		while not __builtin__.Shutdown.isSet() and len(self.menus) != (menu_depth-1):
			
			if 'ButtonSelect' in self.events or 'ButtonForward' in self.events:
				self.events.pop('ButtonSelect',None)
				self.events.pop('ButtonForward',None)
				item = self.MenuCurr().GetItem()[1]
				if item == None:
					pass
				elif type(item) is dict:
					# CME TODO: Nested menus
					pass
				else:
					self.MenuCurr().Paused = True
					param = self.MenuCurr().GetItem()[0] # menu text
					if len(self.MenuCurr().GetItem()) > 2: # menu param
						param = self.MenuCurr().GetItem()[2]
					if item(param) == 1:
						self.HandleBack() # function indicated menu should close
					else:
						self.events = {} # ignore any lingering events
						self.display_offset = 0 # reset active item offset
						self.display_offset_timer = time.time() # reset active item offset timer
						self.MenuPrint() # redraw just in case
					self.MenuCurr().Paused = False
				
			if 'ButtonBack' in self.events:
				self.events.pop('ButtonBack',None)
				if menu_depth > 1:
					self.menus.pop()
					self.MenuPrint()
					
			if len(self.MenuCurr().GetItem()[0]) > self.display_width - 2:
				if (self.display_offset_timer + 1.25) <= time.time():
					self.display_offset += 1
					if self.display_offset >= len(self.MenuCurr().GetItem()[0]):
						self.display_offset = 0
					self.MenuPrint(self.MenuCurr().CalcLineCurr())
					self.display_offset_timer = time.time() - 1
					
			if (self.last_event + 5) <= time.time() and __builtin__.PlaybackModule != None and __builtin__.PlaybackModule.IsLoaded():
				self.DisplayTrack()
				self.MenuPrint()
				
			time.sleep(0.05)
			
		self.events = {}
		return 1
		
		
	def DisplayTrack(self):
		self.Clear()
		self.events = {}
		self.MenuCurr().Paused = True
		
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
				if 'artist' in status_new and 'title' in status_new:
					if self.display_height == 3:
						self.PrintLine(0, status_new['artist'])
						self.PrintLine(1, status_new['title'])
						
					out_time = '>' if __builtin__.PlaybackModule.IsPlaying() else '#'
					out_time += ' ' + status_new['elapsed_display']
					if status_new['length'] > 0:
						out_time += ' / ' + status_new['length_display']
					self.PrintLine(self.display_height-1, out_time)
				
				status_curr = status_new
				
			time.sleep(0.01)
			
		self.MenuCurr().Paused = False
		self.events = {}
		return 0
		
		
	@abc.abstractmethod
	def Clear(self):
		pass
		
	@abc.abstractmethod
	def PrintLine(self, line, str):
		pass
		
		
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
		
	def PrintLine(self, line, text):
		dot3k.lcd.set_cursor_position(0, line)
		dot3k.lcd.write(text[:self.display_width].ljust(self.display_width))