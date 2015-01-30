import os
import sys
import time

import Player

playback_module = Player.PlaybackModules.VLCPlayback()
playback_module.Add("Peppy--The-Firing-Squad_YMXB-160.mp3")
playback_module.Add("Peppy--The-Firing-Squad_YMXB-160.mp3")
playback_module.Play()
time.sleep(5)
playback_module.Next()
time.sleep(5)
playback_module.Stop()