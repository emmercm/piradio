import os
import sys
import time

import Player

playback_module = Player.PlaybackModules.VLCPlayback()
playback_module.Open("Peppy--The-Firing-Squad_YMXB-160.mp3")
playback_module.Play()
time.sleep(10)
playback_module.Stop()