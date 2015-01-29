from Player import OutputDevice

import vlc

class PiAudioOutput(OutputDevice.OutputDevice):
	def __init__(self, *args):
		self.instance = vlc.Instance()
		self.player = self.instance.media_player_new()
		
	def Open(self, filename):
		self.player.set_media(self.instance.media_new(filename))