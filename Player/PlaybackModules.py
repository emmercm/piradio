"""
This is the abstract class for all PlaybackModules.
All PlaybackModules need to implement the @abstractmethods in order to function.
"""

import __builtin__
import abc

class PlaybackModule(object):
	__metaclass__ = abc.ABCMeta
	
	@abc.abstractmethod
	def Menu(self):
		return
	
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
		
	@abc.abstractmethod
	def SetVol(self, vol):
		return
		
	def IsPlaying(self):
		return false
		
		
"""
This is the PlaybackModule for libvlc (via vlc.py).
This module should support the majority of common file formats.
"""

from lib import vlc

class VLCPlayback(PlaybackModule):
	def __init__(self, *args):
		# CME NOTE: After a clean install of pulseaudio on raspbian VLC stops working. Force ALSA to potentially fix.
		self.vlc_instance = vlc.Instance('--aout alsa')
		
		# vlc.MediaListPlayer used for Play()/Pause()/Stop()/Prev()/Next()
		self.vlc_list_player = self.vlc_instance.media_list_player_new()
		
		# vlc.MediaPlayer used for SetVol()
		self.vlc_player = self.vlc_instance.media_player_new()
		self.vlc_list_player.set_media_player(self.vlc_player)
		
		# vlc.MediaList used for Add()
		self.vlc_playlist = self.vlc_instance.media_list_new()
		self.vlc_list_player.set_media_list(self.vlc_playlist)
		
	def Menu(self):
		if __builtin__.OutputDisplay != None:
			__builtin__.OutputDisplay.DisplayMenu({'Dummy':self.Dummy, '652f573730ca0206b5e1c3a99229639f':self.Dummy, 'a8d0bc4ad343f0785353e4eb6f81f93a':self.Dummy, '73e6b069a1d0ed26bdff63b8da16236e':self.Dummy, 'f9a44154a334d4c54916f392fff5c994':self.Dummy})
	def Dummy(self):
		return
		
	def Add(self, mrl):
		media = self.vlc_instance.media_new(mrl)
		self.vlc_playlist.add_media(media)
		
	def Play(self):
		self.vlc_list_player.play()
	def Pause(self):
		self.vlc_list_player.pause()
	def Stop(self):
		self.vlc_list_player.stop()
	def Prev(self):
		if self.vlc_list_player.previous() == -1:
			self.Stop()
	def Next(self):
		if self.vlc_list_player.next() == -1:
			self.Stop()
			
	def SetVol(self, vol):
		self.vlc_player.audio_set_volume(vol)  # 0-100
		
	def IsPlaying(self):
		return self.vlc_list_player.is_playing()