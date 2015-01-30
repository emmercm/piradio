import os
import sys
import time

import Player
import WebServer

PlaybackModule = None
CherryServer = None


if __name__ == '__main__':
	CherryServer = WebServer.WebServer.Server()
	CherryServer.start()
	
	PlaybackModule = Player.PlaybackModules.VLCPlayback()
	PlaybackModule.Add("Peppy--The-Firing-Squad_YMXB-160.pls")
	PlaybackModule.Play()
	# time.sleep(10)
	# PlaybackModule.Next()
	# time.sleep(10)
	# PlaybackModule.Next()
	# time.sleep(10)
	# PlaybackModule.Stop()
	
	raw_input("Press Enter to stop")
		
	CherryServer.stop()
	CherryServer.join()