import math

class Menu(object):
	def __init__(self, menu, *args):
		self.menu = menu
		self.curr = 0
		
	def GetLines(self, lines):
		line_start = self.curr - math.floor(lines-1)
		if line_start < 0: line_start = 0
		line_end = line_start + lines
		
		items = sorted(self.menu.keys())
		for i, item in enumerate(items):
			if i == self.curr:
				items[i] = '> ' + items[i]
			else:
				items[i] = '  ' + items[i]
		return items[line_start:line_end]
		
		
"""
This is the abstract class for all OutputDisplays.
All OutputDisplays need to implement the @abstractmethods in order to function.
"""

import abc

class OutputDisplay(object):
	__metaclass__ = abc.ABCMeta
	
	def __init__(self, *args):
		self.Clear()
		self.display_height = 0
		self.display_width = 0
		
	def DisplayMenu(self, menu):
		print menu
		menu_obj = Menu(menu)
		menu_lines = menu_obj.GetLines(self.display_height)
		for i, line in enumerate(menu_lines):
			self.PrintLine(i, line)
			
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

import os
import subprocess
import sys

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
		
		dot3k.backlight.rgb(255,255,255)
		
		return
		
		# basic backlight.py
		dot3k.lcd.clear()
		dot3k.lcd.write("Hello World")
		# dot3k.backlight.rgb(255,255,255)
		dot3k.backlight.left_rgb(255,0,0)
		dot3k.backlight.right_rgb(0,255,0)
		dot3k.backlight.mid_rgb(0,0,255)
		
		# basic bargraph.py
		# dot3k.backlight.rgb(0,0,0)
		import time
		for i in range(100):
			dot3k.backlight.set_graph(i/100.0)
			time.sleep(0.05)
		for i in range(256):
			dot3k.backlight.set_bar(0,[255-i]*9)
			time.sleep(0.01)
		dot3k.backlight.set_graph(0)
		
		# basic joystick.py
		@dot3k.joystick.on(dot3k.joystick.UP)
		def handle_up(pin):
			print("Up pressed!")
			dot3k.lcd.clear()
			dot3k.backlight.rgb(255,0,0)
			dot3k.lcd.write("Up up and away!")
		@dot3k.joystick.on(dot3k.joystick.DOWN)
		def handle_down(pin):
			print("Down pressed!")
			dot3k.lcd.clear()
			dot3k.backlight.rgb(0,255,0)
			dot3k.lcd.write("Down down doobie down!")
		@dot3k.joystick.on(dot3k.joystick.LEFT)
		def handle_left(pin):
			print("Left pressed!")
			dot3k.lcd.clear()
			dot3k.backlight.rgb(0,0,255)
			dot3k.lcd.write("Leftie left left!")
		@dot3k.joystick.on(dot3k.joystick.RIGHT)
		def handle_right(pin):
			print("Right pressed!")
			dot3k.lcd.clear()
			dot3k.backlight.rgb(0,255,255)
			dot3k.lcd.write("Rightie tighty!")
		@dot3k.joystick.on(dot3k.joystick.BUTTON)
		def handle_button(pin):
			print("Button pressed!")
			dot3k.lcd.clear()
			dot3k.backlight.rgb(255,255,255)
			dot3k.lcd.write("Ouch!")
			
		# advanced backlight.py
		pirate = [
			[0x00,0x1f,0x0b,0x03,0x00,0x04,0x11,0x1f],
			[0x00,0x1f,0x16,0x06,0x00,0x08,0x03,0x1e],
			[0x00,0x1f,0x0b,0x03,0x00,0x04,0x11,0x1f],
			[0x00,0x1f,0x05,0x01,0x00,0x02,0x08,0x07]
		]
		def get_anim_frame(anim, fps):
			return anim[ int(round(time.time()*fps) % len(anim)) ]
		dot3k.lcd.set_cursor_position(1,0)
		dot3k.lcd.write('Display-o-tron')
		dot3k.lcd.write(' ' + chr(0) + '3000 ')
		dot3k.lcd.create_char(0,get_anim_frame(pirate,4))
		# while 1:
		dot3k.backlight.rgb(255,0,0)
		time.sleep(1)
		dot3k.backlight.rgb(0,255,0)
		time.sleep(1)
		dot3k.backlight.rgb(0,0,255)
		time.sleep(1)
		dot3k.backlight.rgb(255,255,255)
		time.sleep(1)
		for i in range(0,360):
			dot3k.backlight.hue(i/360.0)
			time.sleep(0.01)
		for i in range(0,360):
			dot3k.backlight.sweep(i/360.0)
			time.sleep(0.01)
			
		# advanced animations.py
		import datetime, psutil
		dot3k.lcd.write(chr(0) + 'Ooo! Such time' + chr(0))
		dot3k.lcd.set_cursor_position(0,2)
		dot3k.lcd.write(chr(1) + chr(4) + ' Very Wow! ' + chr(3) + chr(2) + chr(5))
		pirate = [
			[0x00,0x1f,0x0b,0x03,0x00,0x04,0x11,0x1f],
			[0x00,0x1f,0x16,0x06,0x00,0x08,0x03,0x1e],
			[0x00,0x1f,0x0b,0x03,0x00,0x04,0x11,0x1f],
			[0x00,0x1f,0x05,0x01,0x00,0x02,0x08,0x07]
		]
		heart = [
			[0x00,0x0a,0x1f,0x1f,0x1f,0x0e,0x04,0x00],
			[0x00,0x00,0x0a,0x0e,0x0e,0x04,0x00,0x00],
			[0x00,0x00,0x00,0x0e,0x04,0x00,0x00,0x00],
			[0x00,0x00,0x0a,0x0e,0x0e,0x04,0x00,0x00]
		]
		raa = [
			[0x1f,0x1d,0x19,0x13,0x17,0x1d,0x19,0x1f],
			[0x1f,0x17,0x1d,0x19,0x13,0x17,0x1d,0x1f],
			[0x1f,0x13,0x17,0x1d,0x19,0x13,0x17,0x1f],
			[0x1f,0x19,0x13,0x17,0x1d,0x19,0x13,0x1f]
		]
		arr = [
			[31,14,4,0,0,0,0,0],
			[0,31,14,4,0,0,0,0],
			[0,0,31,14,4,0,0,0],
			[0,0,0,31,14,4,0,0],
			[0,0,0,0,31,14,4,0],
			[0,0,0,0,0,31,14,4],
			[4,0,0,0,0,0,31,14],
			[14,4,0,0,0,0,0,31]
		]
		char = [
			[12,11,9,9,25,25,3,3],
			[0,15,9,9,9,25,27,3],
			[3,13,9,9,9,27,27,0],
			[0,15,9,9,9,25,27,3]
		]
		pacman = [
			[0x0e,0x1f,0x1d,0x1f,0x18,0x1f,0x1f,0x0e],
			[0x0e,0x1d,0x1e,0x1c,0x18,0x1c,0x1e,0x0f]
		]
		def getAnimFrame(char,fps):
			return char[ int(round(time.time()*fps) % len(char)) ]
		cpu_sample_count = 200
		cpu_samples = [0] * cpu_sample_count
		hue = 0.0
		while True:
			hue += 0.008
			dot3k.backlight.sweep(hue)
			#dot3k.backlight.rgb(0,0,255)
			cpu_samples.append(psutil.cpu_percent() / 100.0)
			cpu_samples.pop(0)
			cpu_avg = sum(cpu_samples) / cpu_sample_count
			dot3k.backlight.set_graph(cpu_avg)
			if hue > 1.0:
				hue = 0.0
				break
			dot3k.lcd.create_char(0,getAnimFrame(char,4))
			dot3k.lcd.create_char(1,getAnimFrame(arr,16))
			dot3k.lcd.create_char(2,getAnimFrame(raa,8))
			dot3k.lcd.create_char(3,getAnimFrame(pirate,2))
			dot3k.lcd.create_char(4,getAnimFrame(heart,4))
			dot3k.lcd.create_char(5,getAnimFrame(pacman,3))
			dot3k.lcd.set_cursor_position(0,1)
			t = datetime.datetime.now().strftime("%H:%M:%S.%f")
			dot3k.lcd.write(t)
			
		# exit
		dot3k.lcd.clear()
		dot3k.backlight.rgb(0,0,0)
		dot3k.backlight.set_graph(0)
		
	def Clear(self):
		dot3k.lcd.clear()
		
	def PrintLine(self, line, str):
		dot3k.lcd.set_cursor_position(0, line)
		dot3k.lcd.write(str[:self.display_width])
		return