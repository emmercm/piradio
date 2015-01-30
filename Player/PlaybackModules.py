import time


import abc
class PlaybackModule(object):
	__metaclass__ = abc.ABCMeta
	
	@abc.abstractmethod
	def Add(self, filename):
		return
	
	@abc.abstractmethod
	def Play(self):
		return
	@abc.abstractmethod
	def Pause(self):
		return
	@abc.abstractmethod
	def Stop(self):
		return
	@abc.abstractmethod
	def Prev(self):
		return
	@abc.abstractmethod
	def Next(self):
		return
		
	# @abc.abstractmethod
	# def SetVolume(self, vol):
		# return
		
		
from lib import vlc
class VLCPlayback(PlaybackModule):
	def __init__(self, *args):
		# CME NOTE: After a clean install of pulseaudio on raspbian VLC stops working. Force ALSA to potentially fix.
		self.vlc_instance = vlc.Instance('--aout alsa')
		self.vlc_playlist = self.vlc_instance.media_list_new()
		self.vlc_player = self.vlc_instance.media_list_player_new()
		self.vlc_player.set_media_list(self.vlc_playlist)
		
	def Add(self, filename):
		media = self.vlc_instance.media_new(filename)
		self.vlc_playlist.add_media(media)
		
	def Play(self):
		self.vlc_player.play()
	def Pause(self):
		self.vlc_player.pause()
	def Stop(self):
		self.vlc_player.stop()
	def Prev(self):
		if self.vlc_player.previous() == -1:
			self.Stop()
	def Next(self):
		if self.vlc_player.next() == -1:
			self.Stop()