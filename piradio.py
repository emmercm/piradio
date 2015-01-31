import __builtin__
import os
import sys
import time

import Player
import WebServer

__builtin__.PlaybackModule = None
__builtin__.CherryServer = None


if __name__ == '__main__':
	__builtin__.CherryServer = WebServer.WebServer.Server()
	__builtin__.CherryServer.start()
	
	__builtin__.PlaybackModule = Player.PlaybackModules.VLCPlayback()
	__builtin__.PlaybackModule.Add("Peppy--The-Firing-Squad_YMXB-160.pls")
	# __builtin__.PlaybackModule.Play()
	# time.sleep(10)
	# __builtin__.PlaybackModule.Next()
	# time.sleep(10)
	# __builtin__.PlaybackModule.Next()
	# time.sleep(10)
	# __builtin__.PlaybackModule.Stop()
	
	print PlaybackModule()
	
	raw_input("Press Enter to stop")
		
	__builtin__.CherryServer.stop()
	__builtin__.CherryServer.join()