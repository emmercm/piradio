import __builtin__
import abc
import math
from natsort import natsorted, ns
import os
import subprocess
import re
import threading
import time
import xml.etree.ElementTree as ET


"""
This is the abstract class for all PlaybackModules.
All PlaybackModules need to implement the @abstractmethods in order to function.
"""

class PlaybackModule(object):
	__metaclass__ = abc.ABCMeta
	
	# self.track alias to __builtin__.Status['TrackInfo']
	def track_get(self):
		return __builtin__.Status['TrackInfo']
	def track_set(self, value):
		__builtin__.Status['TrackInfo'] = value
	track = property(track_get, track_set)
	
	# self.playlist alias to __builtin__.Status['Playlist']
	def playlist_get(self):
		return __builtin__.Status['Playlist']
	def playlist_set(self, value):
		__builtin__.Status['Playlist'] = value
	playlist = property(playlist_get, playlist_set)
	
	
	def __init__(self, *args):
		pass
		
	# Cleanly stop and exit the module
	# Note: child functions should call this at the end
	@abc.abstractmethod
	def Exit(self):
		# Reset track and playlist information
		self.track = self.FormatInfo({})
		self.playlist = []
	
	# Add an item to the current playlist
	# Note: child functions should probably call self.RefreshPlaylist() as a result of this
	@abc.abstractmethod
	def Add(self, filename):
		pass
	# Add a list of items to the current playlist and refresh playlist information
	def AddList(self, items):
		for item in items:
			self.Add(item)
		self.RefreshPlaylist()
	# Remove all items in the current playlist
	@abc.abstractmethod
	def RemoveAll(self):
		pass
	
	# Play/resume playback of the current track or specified track
	@abc.abstractmethod
	def Play(self, index=None):
		pass
	# Pause playback of the current track
	@abc.abstractmethod
	def Pause(self):
		pass
	# Toggle play/pause playback of the current track
	def Toggle(self):
		if self.IsPlaying():
			self.Pause()
		else:
			self.Play()
	# Stop playback
	@abc.abstractmethod
	def Stop(self):
		pass
	# Play the previous song in the playlist
	@abc.abstractmethod
	def Prev(self):
		pass
	# Play the next song in the playlist
	@abc.abstractmethod
	def Next(self):
		pass
		
	# Seek to a specific point in the current track (in seconds)
	@abc.abstractmethod
	def Seek(self, sec):
		pass
		
	# Set the playback volume
	@abc.abstractmethod
	def SetVol(self, vol):
		pass
		
	# Refresh metadata for the current track
	def RefreshTrack(self):
		if self.IsLoaded():
			self.track = self.QueryTrack()
	# Refresh metadata for the current playlist
	def RefreshPlaylist(self):
		if self.IsLoaded():
			self.playlist = self.QueryPlaylist(self)
	# Query metadata for the current track
	@abc.abstractmethod
	def QueryTrack(self):
		pass
	# Query metadata for the current playlist
	@abc.abstractmethod
	def QueryPlaylist(self):
		pass
		
	# Format/force/clamp metadata for a track
	def FormatInfo(self, info):
		return PlaybackModule._FormatInfo(info)
	@staticmethod
	def _FormatInfo(info):
		def FormatTime(sec):
			sec = int(sec)
			if sec < 0: sec = 0
			out = ""
			if sec >= 3600: # >=1 hour
				out += str(sec/3600)
				sec -= (sec/3600) * 3600
				out += ":" + str(sec/60).zfill(2)
			else: # <1 hour
				out += str(sec/60)
			out += ":" + str(sec%60).zfill(2)
			return out
		if not 'playing' in info or info['playing'] == None: info['playing'] = False
		if not 'artist' in info or info['artist'] == None: info['artist'] = 'Unknown Artist'
		if not 'title' in info or info['title'] == None: info['title'] = 'Unknown Track'
		if not 'album' in info or info['album'] == None: info['album'] = 'Unknown Album'
		if not 'index' in info or info['index'] == None: info['index'] = -1
		
		if not 'length' in info or info['length'] == None: info['length'] = 0
		if info['length'] < 0: info['length'] = 0
		info['length_display'] = FormatTime(info['length'])
		
		if not 'elapsed' in info or info['elapsed'] == None: info['elapsed'] = 0
		if info['elapsed'] < 0: info['elapsed'] = 0
		if info['length'] > 0 and info['elapsed'] > info['length']: info['elapsed'] = info['length']
		info['elapsed_display'] = FormatTime(info['elapsed'])
		
		return info
		
	# Is the module currently playing a track
	@abc.abstractmethod
	def IsPlaying(self):
		pass
		
	# Are there tracks loaded in the current playlist
	@abc.abstractmethod
	def IsLoaded(self):
		pass
		
		
"""
This is the PlaybackModule for VLC/libvlc (via vlc.py).
This module should support the majority of common file formats.
"""

from lib import vlc

class VLCPlayback(PlaybackModule):
	def __init__(self, *args):
		# Note: After a clean install of pulseaudio on raspbian VLC stops working. Force ALSA to potentially fix.
		self.vlc_instance = vlc.Instance('--aout alsa')
		
		# vlc.MediaListPlayer used for Play()/Pause()/Stop()/Prev()/Next()
		self.vlc_list_player = self.vlc_instance.media_list_player_new()
		
		# vlc.MediaPlayer used for SetVol()
		self.vlc_player = self.vlc_instance.media_player_new()
		self.vlc_list_player.set_media_player(self.vlc_player)
		
		# vlc.MediaList used for Add()
		self.vlc_playlist = self.vlc_instance.media_list_new()
		self.vlc_list_player.set_media_list(self.vlc_playlist)
		
		# vlc.MediaPlayer vlc.EventManager used for events
		self.vlc_player__events = self.vlc_player.event_manager()
		self.vlc_player__events.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.OnLengthChanged, None)
		self.vlc_player__events.event_attach(vlc.EventType.MediaPlayerMediaChanged, self.OnRefreshTrack, None)
		self.vlc_player__events.event_attach(vlc.EventType.MediaPlayerPositionChanged, self.OnRefreshTrack, None)
		self.vlc_player__events.event_attach(vlc.EventType.MediaPlayerPlaying, self.OnRefreshTrack, None)
		self.vlc_player__events.event_attach(vlc.EventType.MediaPlayerPaused, self.OnRefreshTrack, None)
		
		super(VLCPlayback, self).__init__(*args)
		
	def Exit(self):
		self.Stop()
		# Unregister vlc.MediaPlayer events
		self.vlc_player__events.event_detach(vlc.EventType.MediaPlayerLengthChanged)
		self.vlc_player__events.event_detach(vlc.EventType.MediaPlayerMediaChanged)
		self.vlc_player__events.event_detach(vlc.EventType.MediaPlayerPositionChanged)
		self.vlc_player__events.event_detach(vlc.EventType.MediaPlayerPlaying)
		self.vlc_player__events.event_detach(vlc.EventType.MediaPlayerPaused)
		super(VLCPlayback, self).Exit()
		
	def OnLengthChanged(self, *args, **kwds):
		self.RefreshPlaylist() # a length changed, update full playlist
		self.RefreshTrack()
	def OnRefreshTrack(self, *args, **kwds):
		self.RefreshTrack()
		
	# Add an item to the current playlist
	def Add(self, mrl):
		media = self.vlc_instance.media_new(mrl)
		self.vlc_playlist.add_media(media)
		
	# Remove all items in the current playlist
	def RemoveAll(self):
		self.vlc_playlist.lock()
		for i in range(self.vlc_playlist.count()):
			self.vlc_playlist.remove_index(0)
		self.vlc_playlist.unlock()
		
	# Play/resume playback of the current track or specified track
	def Play(self, index=None):
		if index == None:
			self.vlc_list_player.play()
		else:
			# Note: Can't use play_item_at_index() because it doesn't take playlists into account
			self.vlc_list_player.play_item( self.GetMediaList()[int(index)] )
	# Pause playback of the current track
	def Pause(self):
		if self.IsPlaying(): # pause() toggles playback, check is necessary
			self.vlc_list_player.pause()
	# Stop playback
	def Stop(self):
		self.vlc_list_player.stop()
	# Play the previous song in the playlist, stop if fail
	def Prev(self):
		if self.vlc_list_player.previous() == -1:
			self.Stop()
	# Play the next song in the playlist, stop if fail
	def Next(self):
		if self.vlc_list_player.next() == -1:
			self.Stop()
			
	# Seek to a specific point in the current track (in seconds)
	def Seek(self, sec):
		self.vlc_player.set_time( int(math.floor(sec*1000)) )
		
	# Set the playback volume (0-100)
	def SetVol(self, vol):
		self.vlc_player.audio_set_volume(vol)
		
		
	# Query metadata for the current track
	def QueryTrack(self):
		media = self.vlc_player.get_media()
		info = self.GetMeta(media)
		if self.vlc_player != None:
			info['elapsed'] = int(math.floor(self.vlc_player.get_time() / 1000))
		info['index'] = self.vlc_playlist.index_of_item(media)
		if info['index'] == -1: # media is probaly a subitem, get index based on MRL
			items = self.GetMediaList()
			for idx, item in enumerate(items):
				if item.get_mrl() == media.get_mrl():
					info['index'] = idx
					break
		return self.FormatInfo(info)
		
	# Query metadata for the given track
	def GetMeta(self, media):
		info = {}
		if media != None:
			if not media.is_parsed():
				media.parse()
			info['playing'] = (media.get_state() == vlc.State.Playing)
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
	def QueryPlaylist(self, playlist=None):
		items = self.GetMediaList()
		for idx, media in enumerate(items):
			if not media.is_parsed():
				media.parse()
			items[idx] = self.GetMeta(media)
		return items
		
	# Get all items in the playlist
	def GetMediaList(self, playlist=None):
		if playlist == None: # start processing with current playlist
			playlist = self.vlc_playlist
		items = []
		for i in range(0, playlist.count()):
			media = playlist.item_at_index(i)
			if media.subitems() != None: # item has subitems (playlist?) (doesn't get parsed until played)
				items.extend( self.GetMediaList(media.subitems()) )
			else: # item is standalone
				items.append( media )
		return items
		
	# Is the module currently playing a track
	def IsPlaying(self):
		return self.vlc_list_player.is_playing()
		
	# Are there tracks loaded in the current playlist
	def IsLoaded(self):
		count = self.vlc_playlist.count() # should be .lock()ed first, seems to cause infinite hang
		return (count > 0)
		
		
	browse_path = '/'
	
	# Display a list of: root folder, attached USB drives
	def Menu_Local(item):
		# A folder/file was selected
		def Menu_Browse(item):
			if item[:2] == '..': return 1 # quit menu (go up a level)
			item_path = os.path.abspath(os.path.join(VLCPlayback.browse_path, item))
			
			# A folder was selected, list its contents
			if os.path.isdir(item_path):
				VLCPlayback.browse_path = item_path
				menu = [('../',Menu_Browse)]
				for dirpath, dirnames, filenames in os.walk(VLCPlayback.browse_path):
					files = dirnames + filenames
					files = natsorted(files,alg=ns.PATH)
					for file in files:
						if file[:1] == '.': continue # hidden file
						if os.path.isdir(os.path.join(dirpath,file)):
							menu.append( (file+'/',Menu_Browse) )
						else:
							if re.search('(?i).+\.((3gp|aiff|aac|au|flac|m4a|m4p|mid|mka|mp3|mpc|oga|ogg|ra|rm|snd|tta|wav|wma|wv)|(asx|m3u8?|pls|sa?mi|wpl|xspf))$', file) == None: continue # regex: ((files)|(playlists))
							menu.append( (file,Menu_Browse) )
					break
					
				__builtin__.OutputDisplay.DisplayMenu(menu, 1)
				VLCPlayback.browse_path = os.path.abspath(os.path.join(VLCPlayback.browse_path, '..'))
				
			# A file was selected, start playback of it
			else:
				if not type(__builtin__.PlaybackModule) is VLCPlayback:
					# Switch global playback module
					if __builtin__.PlaybackModule != None:
						__builtin__.PlaybackModule.Exit()
					__builtin__.PlaybackModule = VLCPlayback()
				else:
					# Stop and clear the current playlist
					__builtin__.PlaybackModule.Stop()
					__builtin__.PlaybackModule.RemoveAll()
					
				# Find all other media files in the same directory
				files = []
				for (dirpath, dirnames, filenames) in os.walk(VLCPlayback.browse_path):
					for file in filenames:
						if file[:1] == '.': continue
						if re.search('(?i).+\.(3gp|aiff|aac|au|flac|m4a|m4p|mid|mka|mp3|mpc|oga|ogg|ra|rm|snd|tta|wav|wma|wv)$', file) == None: continue # regex: (files)
						files.append(os.path.abspath(os.path.join(VLCPlayback.browse_path, file)))
					break
				files = natsorted(files,alg=ns.PATH)
				if item_path in files: # file selected, add all media files to current playlist
					__builtin__.PlaybackModule.AddList(files)
					__builtin__.PlaybackModule.Play(files.index(item_path))
				else: # playlist selected, add only it to the current playlist
					__builtin__.PlaybackModule.AddList([item_path])
					__builtin__.PlaybackModule.Play()
				
				__builtin__.OutputDisplay.DisplayTrack()
				
		# A USB device was selected, mount it and browse into it
		def Menu_USB(dev):
			# Get 'mounted' status
			mounted = False
			try:
				mounted = (subprocess.check_output('mount | grep ^'+dev, shell=True) != '')
			except subprocess.CalledProcessError:
				pass
			mount = os.path.join('/mnt',os.path.basename(dev))
			# Unmount
			if os.path.exists(mount):
				try:
					subprocess.check_output('sudo umount '+mount, shell=True)
				except subprocess.CalledProcessError:
					pass
			else:
				os.makedirs(mount)
			# Mount
			try:
				subprocess.check_output('mount '+dev+' '+mount, shell=True)
			except subprocess.CalledProcessError:
				pass
			# Browse
			return Menu_Browse(mount)
			
			
		menu = [('/',Menu_Browse)]
		
		# --- Enumerate /dev/sd* USB drives ---
		def cat(file):
			f = open(file, 'r')
			s = f.read().rstrip()
			f.close()
			return s
		def sizeof_fmt(num, suffix='B'): # http://stackoverflow.com/a/1094933
			for unit in ['','K','M','G','T','P','E','Z']:
				if abs(num) < 1024.0:
					return "%3.1f%s%s" % (num, unit, suffix)
				num /= 1024.0
			return "%.1f%s%s" % (num, 'Yi', suffix)
		# Find /sys/block/sd* devices
		for syspath, blocks, null in os.walk('/sys/block'):
			for block in sorted(blocks):
				if block[:2] == 'sd':
					vendor = cat(os.path.join(syspath,block,'device/vendor'))
					model = cat(os.path.join(syspath,block,'device/model'))
					# Find /sys/block/sd*/sd* partitions
					for blockpath, parts, null in os.walk(os.path.join(syspath,block)):
						for part in sorted(parts):
							if part[:len(block)] == block:
								size = sizeof_fmt(float(cat(os.path.join(blockpath,part,'size')))*512)
								label = vendor+' '+model+' ('+size+')'
								menu.append( (label,Menu_USB,os.path.join('/dev',part)) )
								
		__builtin__.OutputDisplay.DisplayMenu(menu)
		
	Menu = [('Local Media',Menu_Local)]
	
	
"""
This is the PlaybackModule for Pandora (via python-pianobar).
This module supports playback of saved stations for all types of accounts (including free).
"""

from lib import pianobar

class PandoraPlayback(PlaybackModule):
	def __init__(self, *args):
		# Start pianobar (launch process)
		self.pianobar = pianobar.pianobar()
		self.pianobar.Start()
		
		# Pianobar does not provide events, this thread polls for changed track and playlist
		self.stop_refresh = threading.Event()
		class Refresh(threading.Thread):
			def __init__(self, pandora_playback):
				self.pandora_playback = pandora_playback
				threading.Thread.__init__(self)
			def run(self):
				track_old = self.pandora_playback.track
				while not self.pandora_playback.stop_refresh.is_set():
					self.pandora_playback.RefreshTrack()
					if self.pandora_playback.CmpTrack(self.pandora_playback.track, track_old): # refresh playlist on track change
						self.pandora_playback.RefreshPlaylist()
						track_old = self.pandora_playback.track
					time.sleep(0.1)
		refresh = Refresh(self)
		refresh.start()
		
		super(PandoraPlayback, self).__init__(*args)
		
	# Cleanly stop and exit the module
	def Exit(self):
		# Stop the track/playlist polling thread
		self.stop_refresh.set()
		# Clean exit pianobar
		self.pianobar.Exit()
		super(PandoraPlayback, self).Exit()
		
	# Add an item to the current playlist (N/A for Pandora)
	def Add(self, item):
		pass
	# Remove all items in the current playlist (N/A for Pandora)
	def RemoveAll(self):
		pass
		
	# Play/resume playback of the current track
	def Play(self, index=None):
		self.pianobar.Play()
	# Pause playback of the current track
	def Pause(self):
		self.pianobar.Pause()
	# Stop playback (not supported by pianobar)
	def Stop(self):
		pass
	# Play the previous song in the playlist (N/A for Pandora)
	def Prev(self):
		pass
	# Play the next song in the playlist
	def Next(self):
		self.pianobar.Next()
		
	# Seek to a specific point in the current track (in seconds) (N/A for Pandora)
	def Seek(self, sec):
		pass
		
	# Set the playback volume (not implemented)
	def SetVol(self, vol):
		pass
		
		
	# Compare two tracks for artist/title/album
	def CmpTrack(self, t1, t2):
		if not 'artist' in t1 or not 'artist' in t2: return True
		if not 'title' in t1 or not 'title' in t2: return True
		if not 'album' in t1 or not 'album' in t2: return True
		return not (t1['artist'] == t2['artist'] and t1['title'] == t2['title'] and t1['album'] == t2['album'])
		
	# Query metadata for the current track
	def QueryTrack(self):
		info = self.pianobar.GetInfo()
		for idx, item in enumerate(self.playlist):
			if not self.CmpTrack(info, item):
				info['index'] = idx
				break
		return self.FormatInfo(info)
		
	# Call GetMeta() for all playlist items
	def QueryPlaylist(self, playlist=None):
		items = self.pianobar.GetPlaylist()
		for idx, item in enumerate(items):
			items[idx] = self.FormatInfo(item)
		return items
		
	# Is the module currently playing a track
	def IsPlaying(self):
		return self.pianobar.IsPlaying()
		
	# Are there tracks loaded in the current playlist
	def IsLoaded(self):
		return self.pianobar.IsLoaded()
		
		
	# Log in and display user's stations
	def Menu_Login(item):
		# A station was selected, start playback of it
		def Menu_Station(station_id):
			# LCD status message
			__builtin__.OutputDisplay.Clear()
			__builtin__.OutputDisplay.PrintLine(0, 'Starting...')
			# Start station
			if not __builtin__.PlaybackModule.pianobar.ChangeStation(station_id):
				__builtin__.OutputDisplay.DisplayMenu( [('Station error!',None)] ) # menu so it has to be dismissed
				return
			# Display track
			__builtin__.OutputDisplay.DisplayTrack()
			
		if not type(__builtin__.PlaybackModule) is PandoraPlayback:
			# Start pianobar
			__builtin__.OutputDisplay.Clear()
			__builtin__.OutputDisplay.PrintLine(0, 'Logging in...')
			module = PandoraPlayback()
			# Login to pianobar
			xml_pandora = __builtin__.Config.findall('./playback_modules/pandora')[0]
			if not module.pianobar.Login(xml_pandora.findall('email')[0].text, xml_pandora.findall('password')[0].text):
				module = None
				__builtin__.OutputDisplay.DisplayMenu( [('Login failed!',None)] ) # menu so it has to be dismissed
				return
			# Switch global playback module
			if __builtin__.PlaybackModule != None:
				__builtin__.PlaybackModule.Exit()
			__builtin__.PlaybackModule = module
			
		# Print Pandora station list
		if type(__builtin__.PlaybackModule) is PandoraPlayback:
			menu = []
			stations = __builtin__.PlaybackModule.pianobar.ListStations()
			for station in stations:
				menu.append( (station[1],Menu_Station,station[0]) )
				
			__builtin__.OutputDisplay.DisplayMenu(menu)
			
	Menu = [('Pandora',Menu_Login)]
	
	
"""
This is the PlaybackModule for Spotify/libspotify (via pyspotify).
This module supports playback of playlists for premium accounts.
"""

import spotify

class SpotifyPlayback(PlaybackModule):
	def __init__(self, *args):
		self.queue_index = -1
		self.queue = []
		
		# To keep track of elapsed time because libspotify doesn't
		self.time_started = 0
		self.time_paused = 0
		
		# libspotify config
		self.timeout_short = 20
		self.timeout_long = 60
		self.config = spotify.Config()
		for root, dirs, files in os.walk(__builtin__.Directory): # find spotify_appkey.key in subdirectories
			if 'spotify_appkey.key' in files:
				self.config.load_application_key_file( os.path.join(root,'spotify_appkey.key') )
				break
				
		# Start libspotify session / audio sink
		# Only one Session can be created during the entire lifetime of this app, store it in __builtin__
		if not hasattr(__builtin__, 'SpotifySession'):
			__builtin__.SpotifySession = spotify.Session(config=self.config)
			self.audio = spotify.AlsaSink(__builtin__.SpotifySession)
		self.session = __builtin__.SpotifySession
		
		# Register libspotify event handlers
		self.session.on(spotify.SessionEvent.PLAY_TOKEN_LOST, self.OnTokenLost)
		self.session.on(spotify.SessionEvent.END_OF_TRACK, self.OnTrackEnd)
		self.event_loop = spotify.EventLoop(self.session)
		self.event_loop.start()
		
		# spotify.SessionEvent.METADATA_UPDATED doesn't update on playback time, have to use a polling thread
		self.stop_refresh = threading.Event()
		class Refresh(threading.Thread):
			def __init__(self, spotify_playback):
				self.spotify_playback = spotify_playback
				threading.Thread.__init__(self)
			def run(self):
				while not self.spotify_playback.stop_refresh.is_set():
					self.spotify_playback.RefreshTrack()
					time.sleep(0.1)
		refresh = Refresh(self)
		refresh.start()
		
		super(SpotifyPlayback, self).__init__(*args)
		
	# Cleanly stop and exit the module
	def Exit(self):
		self.stop_refresh.set()
		# Unregister libspotify event handlers
		self.event_loop.stop()
		self.session.off(spotify.SessionEvent.PLAY_TOKEN_LOST)
		self.session.off(spotify.SessionEvent.END_OF_TRACK)
		# Clean logout (libspotify does disk things at logout)
		self.session.logout()
		
		super(SpotifyPlayback, self).Exit()
		
	# libspotify event handlers
	def OnTokenLost(self, session):
		self.Pause()
	def OnTrackEnd(self, session):
		self.Next()
		
		
	# Add an item to the current playlist
	# Types accepted: track, album, playlist
	def Add(self, item):
		if type(item) == spotify.Track:
			self.queue += [item]
		elif type(item) == spotify.Album:
			browser = item.browse()
			if browser.is_loaded == False:
				try:
					browser.load(self.timeout_short)
					self.queue += browser.tracks
				except spotify.error.Timeout:
					pass
		elif type(item) == spotify.Playlist:
			self.queue += item.tracks
			
	# Remove all items in the current playlist
	def RemoveAll(self):
		self.queue_index = -1
		self.queue = []
		self.RefreshPlaylist()
		
	# Play/resume playback of the current track or specified track
	def Play(self, index=None):
		# Current queue has not been started yet, "next" to first track
		if index is None and self.queue_index == -1 and len(self.queue) > 0:
			return self.Next()
			
		# Load selected track
		if not index is None: index = int(index)
		if not index is None and 0 <= index and index < len(self.queue):
			self.queue_index = index
			track = self.queue[self.queue_index]
			if track.is_loaded == False:
				try:
					track.load(self.timeout_long)
				except spotify.error.Timeout:
					__builtin__.OutputDisplay.DisplayMenu( [('Error playing!',None)] ) # menu so it has to be dismissed
					return
			self.session.flush_caches()
			if not track.availability is spotify.TrackAvailability.AVAILABLE:
				return False # playback will fail
			self.session.player.load(track)
			
		# Play, handle paused elapsed time
		self.session.player.play()
		if self.time_paused > 0:
			self.time_started = time.time() - (self.time_paused - self.time_started)
			self.time_paused = 0
		else:
			self.time_started = time.time()
		return True
		
	# Pause playback of the current track
	def Pause(self):
		self.session.player.pause()
		self.time_paused = time.time()
		
	# Stop playback
	def Stop(self):
		self.session.player.unload()
		
	# Play the previous song in the playlist (until it doesn't fail)
	def Prev(self):
		self.time_started = 0
		self.time_paused = 0
		if self.queue_index > 0:
			if not self.Play(self.queue_index - 1):
				self.Prev()
		else:
			self.Stop()
	# Play the next song in the playlist (until it doesn't fail)
	def Next(self):
		self.time_started = 0
		self.time_paused = 0
		if self.queue_index < len(self.queue) - 1:
			if not self.Play(self.queue_index + 1):
				self.Next()
		else:
			self.Stop()
			
	# Seek to a specific point in the current track (in seconds)
	def Seek(self, sec):
		self.session.player.seek( int(math.floor(sec*1000)) )
		# Elapsed time calculations
		if self.time_paused > 0:
			self.time_started = time.time() - sec - (self.time_paused - self.time_started)
		else:
			self.time_started = time.time() - sec
			
	# Set the playback volume
	def SetVol(self, vol):
		pass
		
	# Query metadata for the current track
	def QueryTrack(self):
		info = {}
		if 0 <= self.queue_index and self.queue_index < len(self.queue):
			track = self.queue[self.queue_index]
			info = self.GetMeta(track)
		info['index'] = self.queue_index
		return self.FormatInfo(info)
		
	# Query metadata for the current track
	# WARNING: This function can get expensive when called frequently, that's why GetPlaylist() caches metadata
	def GetMeta(self, track):
		info = {}
		if track.is_loaded:
			if track == self.queue[self.queue_index]:
				info['playing'] = self.IsPlaying()
				if self.time_paused > 0:
					info['elapsed'] = int(math.floor(self.time_paused - self.time_started))
				else:
					info['elapsed'] = int(math.floor(time.time() - self.time_started))
			if len(track.artists) > 0:
				artist = track.artists[0]
				if artist.is_loaded:
					info['artist'] = artist.name
			info['title'] = track.name
			album = track.album
			if album.is_loaded:
				info['album'] = album.name
			info['length'] = int(math.floor(track.duration / 1000))
		return self.FormatInfo(info)
		
	# Call GetMeta() for all playlist items
	def QueryPlaylist(self, playlist=None):
		items = []
		for track in self.queue:
			items.append( self.GetMeta(track) )
		return items
		
	# Get all folders/playlists within a certain folder ID (root if not provided)
	def GetPlaylistFolder(self, folder_id=None):
		collection = []
		
		# Load user playlists if not loaded
		if self.session.playlist_container.is_loaded == False:
			try:
				self.session.playlist_container.load(self.timeout_short)
			except spotify.error.Timeout:
				pass
				
		# Find start position if folder ID given
		start = 0
		if folder_id != None:
			for idx, playlist in enumerate(self.session.playlist_container):
				if type(playlist) is spotify.PlaylistFolder and playlist.type is spotify.PlaylistType.START_FOLDER and playlist.id == folder_id:
					start = idx + 1
					break
		# Iterate playlists, don't recurse folders
		depth = 0
		for idx in range(start, len(self.session.playlist_container)):
			playlist = self.session.playlist_container[idx]
			if type(playlist) is spotify.PlaylistFolder:
				if playlist.type is spotify.PlaylistType.START_FOLDER:
					# Folder within the current folder
					if depth == 0:
						collection.append( (playlist.name,playlist) )
					depth += 1
				if playlist.type is spotify.PlaylistType.END_FOLDER:
					depth -= 1
					if depth < 0: break # exiting given folder
			# Playlist within the current folder
			elif type(playlist) is spotify.Playlist and depth == 0:
				if playlist.is_loaded == False:
					try:
						playlist.load(self.timeout_short)
					except spotify.error.Timeout:
						pass
				if playlist.is_loaded == True:
					collection.append( (playlist.name,playlist) )
					
		self.session.flush_caches() # write cache to disk immediately
		return collection
		
	# Is the module currently playing a track
	def IsPlaying(self):
		return self.session.player.state is spotify.PlayerState.PLAYING
		
	# Are there tracks loaded in the current playlist
	def IsLoaded(self):
		return len(self.queue) > 0
		
		
	# Log in and display user's playlists
	def Menu_Login(item):
		# A folder was selected, list all items inside it
		def Menu_Folder(playlist_folder=None):
			if type(playlist_folder) is str and playlist_folder[:2] == '..': return 1 # quit menu (go up a level)
			
			__builtin__.OutputDisplay.Clear()
			__builtin__.OutputDisplay.PrintLine(0, 'Loading...')
			if not playlist_folder is None:
				playlists = __builtin__.PlaybackModule.GetPlaylistFolder(playlist_folder.id)
			else:
				playlists = __builtin__.PlaybackModule.GetPlaylistFolder()
				
			menu = []
			if not playlist_folder is None: # currently in a sub-folder
				menu.append( ('../',Menu_Folder) )
			for playlist in playlists:
				if type(playlist[1]) is spotify.Playlist:
					menu.append( (playlist[0],Play_Playlist,playlist[1]) )
				if type(playlist[1]) is spotify.PlaylistFolder:
					menu.append( (playlist[0]+'/',Menu_Folder,playlist[1]) )
			__builtin__.OutputDisplay.DisplayMenu(menu)
			
		# A playlist was selected, play it
		def Play_Playlist(playlist):
			__builtin__.OutputDisplay.Clear()
			__builtin__.OutputDisplay.PrintLine(0, 'Buffering...')
			__builtin__.PlaybackModule.RemoveAll()
			__builtin__.PlaybackModule.AddList([playlist])
			__builtin__.PlaybackModule.Play()
			__builtin__.OutputDisplay.DisplayTrack()
		
		if not type(__builtin__.PlaybackModule) is SpotifyPlayback:
			# Start Spotify
			__builtin__.OutputDisplay.Clear()
			__builtin__.OutputDisplay.PrintLine(0, 'Logging in...')
			module = SpotifyPlayback()
			# Login to Spotify
			xml_spotify = __builtin__.Config.findall('./playback_modules/spotify')[0]
			if module.session.remembered_user_name == xml_spotify.findall('username')[0].text:
				module.session.relogin()
			else:
				module.session.login(xml_spotify.findall('username')[0].text, xml_spotify.findall('password')[0].text, True)
			module.session.process_events() # wait for login
			while module.session.connection.state is spotify.ConnectionState.OFFLINE: # wait for online
				module.session.process_events()
			if not module.session.connection.state is spotify.ConnectionState.LOGGED_IN:
				module = None
				__builtin__.OutputDisplay.DisplayMenu( [('Login failed!',None)] ) # menu so it has to be dismissed
				return
			module.session.flush_caches() # write login blob to disk
			
			# Load playlist library
			__builtin__.OutputDisplay.Clear()
			__builtin__.OutputDisplay.PrintLine(0, 'Starting...')
			try:
				module.session.playlist_container.load(module.timeout_short)
			except spotify.error.Timeout:
				pass
			if module.session.playlist_container.is_loaded == False:
				module = None
				__builtin__.OutputDisplay.DisplayMenu( [('Start failed!',None)] ) # menu so it has to be dismissed
				return
			module.session.flush_caches() # write playlist cache to disk
			
			# Switch global playback module
			if __builtin__.PlaybackModule != None:
				__builtin__.PlaybackModule.Exit()
			__builtin__.PlaybackModule = module
		
		# Print Spotify playlist list
		if type(__builtin__.PlaybackModule) is SpotifyPlayback:
			Menu_Folder()
			
	Menu = [('Spotify',Menu_Login)]