import __builtin__
import abc
import math
from natsort import natsorted, ns
import os
import re


"""
This is the abstract class for all PlaybackModules.
All PlaybackModules need to implement the @abstractmethods in order to function.
"""

class PlaybackModule(object):
	__metaclass__ = abc.ABCMeta
	
	@abc.abstractmethod
	def Menu(self):
		pass
	
	@abc.abstractmethod
	def Add(self, filename):
		pass
	def AddList(self, items):
		for item in items:
			self.Add(item)
	@abc.abstractmethod
	def RemoveAll(self):
		pass
	
	@abc.abstractmethod
	def Play(self, index=None):
		pass
	@abc.abstractmethod
	def Pause(self):
		pass
	def Toggle(self):
		if self.IsPlaying():
			self.Pause()
		else:
			self.Play()
	@abc.abstractmethod
	def Stop(self):
		pass
	@abc.abstractmethod
	def Prev(self):
		pass
	@abc.abstractmethod
	def Next(self):
		pass
		
	@abc.abstractmethod
	def SetVol(self, vol):
		pass
		
	@abc.abstractmethod
	def GetInfo(self):
		pass
	@abc.abstractmethod
	def GetPlaylist(self):
		pass
	def FormatInfo(self, info):
		def FormatTime(sec):
			if sec < 0: sec = 0
			out = ""
			if sec >= 3600: # >=1 hour
				out += str(sec/3600)
				out += str(sec/60).zfill(2)
			else: # <1 hour
				out += str(sec/60)
			out += ":" + str(sec%60).zfill(2)
			return out
		if not 'playing' in info or info['playing'] == None: info['playing'] = False
		if not 'artist' in info or info['artist'] == None: info['artist'] = 'Unknown Artist'
		if not 'title' in info or info['title'] == None: info['title'] = 'Unknown Track'
		if not 'album' in info or info['album'] == None: info['album'] = 'Unknown Album'
		if not 'elapsed' in info or info['elapsed'] == None: info['elapsed'] = 0
		info['elapsed_display'] = FormatTime(info['elapsed'])
		if not 'length' in info or info['length'] == None: info['length'] = 0
		info['length_display'] = FormatTime(info['length'])
		return info
		
	@abc.abstractmethod
	def IsPlaying(self):
		pass
		
	@abc.abstractmethod
	def IsLoaded(self):
		pass
		
		
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
		
	def Add(self, mrl):
		media = self.vlc_instance.media_new(mrl)
		self.vlc_playlist.add_media(media)
		
	def RemoveAll(self):
		self.vlc_playlist.lock()
		for i in range(self.vlc_playlist.count()):
			self.vlc_playlist.remove_index(0)
		self.vlc_playlist.unlock()
		
	def Play(self, index=None):
		if index == None:
			self.vlc_list_player.play()
		else:
			# CME NOTE: Can't use play_item_at_index() because it doesn't take playlists into account
			self.vlc_list_player.play_item( self.GetMediaList()[int(index)] )
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
		
	def GetInfo(self):
		media = self.vlc_player.get_media()
		info = self.GetMeta(media)
		if self.vlc_player != None:
			info['elapsed'] = int(math.floor(self.vlc_player.get_time() / 1000))
		return self.FormatInfo(info)
		
	def GetMeta(self, media):
		info = {}
		if media != None:
			if not media.is_parsed():
				media.parse()
			info['playing'] = (media.get_state() != vlc.State.NothingSpecial)
			info['artist'] = None
			info['title'] = None
			info['album'] = None
			# Parse vlc.Meta.NowPlaying (if active song)
			if media.get_state() != vlc.State.NothingSpecial:
				now_playing = media.get_meta(vlc.Meta.NowPlaying)
				if now_playing != None:
					now_playing_split = now_playing.split(' - ')
					if len(now_playing_split) >= 2:
						info['artist'] = now_playing_split[0]
						info['title'] = ' - '.join(now_playing_split[1:])
						now_playing = None
					else:
						info['title'] = now_playing
			# Parse other meta tags
			info['artist'] = info['artist'] or media.get_meta(vlc.Meta.Artist)
			info['title'] = info['title'] or media.get_meta(vlc.Meta.Title)
			info['album'] = media.get_meta(vlc.Meta.Album)
			info['length'] = int(math.floor(media.get_duration() / 1000))
		return self.FormatInfo(info)
		
	# Call GetMeta() for all playlist items
	def GetPlaylist(self, playlist=None):
		items = self.GetMediaList()
		for idx, item in enumerate(items):
			items[idx] = self.GetMeta(item)
		return items
		
	# Get all items in the playlist
	def GetMediaList(self, playlist=None):
		if playlist == None: # start processing with current playlist
			playlist = self.vlc_playlist
		items = []
		playlist.lock()
		for i in range(0, playlist.count()):
			media = playlist.item_at_index(i)
			if media.subitems() != None: # item has subitems (playlist?) (doesn't get parsed until played)
				items.extend( self.GetMediaList(media.subitems()) )
			else: # item is standalone
				items.append( media )
		playlist.unlock()
		return items
		
	def IsPlaying(self):
		return self.vlc_list_player.is_playing()
		
	def IsLoaded(self):
		self.vlc_playlist.lock()
		count = self.vlc_playlist.count()
		self.vlc_playlist.unlock()
		return (count > 0)
		
		
	browse_path = '/'
	
	def Menu_Local(item):
		def Menu_Browse(item):
			if item[:2] == '..': return 1 # quit menu (go up a level)
			item_path = os.path.abspath(os.path.join(VLCPlayback.browse_path, item))
			
			if os.path.isdir(item_path):
				VLCPlayback.browse_path = item_path
				menu = {'../':Menu_Browse}
				for (dirpath, dirnames, filenames) in os.walk(VLCPlayback.browse_path):
					for dir in dirnames:
						if dir[:1] == '.': continue
						menu = dict(menu.items() + {dir+'/':Menu_Browse}.items())
					for file in filenames:
						if file[:1] == '.': continue
						if re.search('(?i).+\.((3gp|aiff|aac|au|flac|m4a|m4p|mid|mka|mp3|mpc|oga|ogg|ra|rm|snd|tta|wav|wma|wv)|(asx|m3u8?|pls|sa?mi|wpl|xspf))$', file) == None: continue # regex: ((files)|(playlists))
						menu = dict(menu.items() + {file:Menu_Browse}.items())
					break
					
				__builtin__.OutputDisplay.DisplayMenu(menu, 1)
				VLCPlayback.browse_path = os.path.abspath(os.path.join(VLCPlayback.browse_path, '..'))
				
			else:
				__builtin__.PlaybackModule.Stop()
				__builtin__.PlaybackModule.RemoveAll()
				files = []
				for (dirpath, dirnames, filenames) in os.walk(VLCPlayback.browse_path):
					for file in filenames:
						if file[:1] == '.': continue
						if re.search('(?i).+\.(3gp|aiff|aac|au|flac|m4a|m4p|mid|mka|mp3|mpc|oga|ogg|ra|rm|snd|tta|wav|wma|wv)$', file) == None: continue # regex: (files)
						files.append(os.path.abspath(os.path.join(VLCPlayback.browse_path, file)))
					break
				files = natsorted(files,alg=ns.PATH)
				if item_path in files: # file
					__builtin__.PlaybackModule.AddList(files)
					__builtin__.PlaybackModule.Play(files.index(item_path))
				else: # playlist
					__builtin__.PlaybackModule.Add(item_path)
					__builtin__.PlaybackModule.Play()
				
				__builtin__.OutputDisplay.DisplayTrack()
				
		menu = {'/':Menu_Browse}
		__builtin__.OutputDisplay.DisplayMenu(menu)
		
	Menu = {'Local Media': Menu_Local}