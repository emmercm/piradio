import __builtin__
import os
import sys
import time

import Player
import WebServer

__builtin__.PlaybackModule = None
__builtin__.CherryServer = None


if __name__ == '__main__':
	# Start CherryPy thread
	__builtin__.CherryServer = WebServer.WebServer.Server()
	__builtin__.CherryServer.start()
	
	# DEBUG
	__builtin__.PlaybackModule = Player.PlaybackModules.VLCPlayback()
	__builtin__.PlaybackModule.Add("Peppy--The-Firing-Squad_YMXB-160.pls")
	
	# Main loop
	raw_input("Press Enter to stop")
	
	# Exit/cleanup
	if __builtin__.PlaybackModule != None: __builtin__.PlaybackModule.Stop()
	__builtin__.CherryServer.stop()
	__builtin__.CherryServer.join()