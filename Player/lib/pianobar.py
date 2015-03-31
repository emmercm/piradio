import datetime
import pexpect
import re

class pianobar(object):
	_pianobar = None
	
	_station = None
	_playing = False
	
	def __init__(self, *args):
		pass
		
	def Start(self):
		self._pianobar = pexpect.spawn("pianobar")
		try:
			self._pianobar.expect_exact("Welcome to pianobar", timeout=5)
		except pexpect.ExceptionPexpect:
			return False
		return True
			
	def Exit(self):
		self._station = None
		self._playing = False
		return self.Send("q") # quits completely, no need for pexpect.close()
		
		
	def IsLoaded(self):
		return (self._station != None and self.IsRunning())
		
	def IsRunning(self):
		try:
			return self._pianobar.isalive()
		except pexpect.ExceptionPexpect:
			return False
			
	def IsPlaying(self):
		return self._playing
		
		
	def ExpectLines(self, lines):
		buffer = ""
		try:
			buffer = ""
			for i in range(1, lines):
				endl = self._pianobar.expect_exact(["\r\n","\r"], timeout=1)
				buffer += self._pianobar.before
				if endl == 0:
					buffer += "\r\n"
				elif endl == 1:
					buffer += "\r"
		except pexpect.ExceptionPexpect:
			pass
		return buffer
			
	def Send(self, str):
		try:
			self._pianobar.send(str)
			return True
		except pexpect.ExceptionPexpect:
			return False
			
		
	def Play(self):
		if self.Send("P"):
			self._playing = True
			return True
		return False
			
	def Pause(self):
		if self.Send("S"):
			self._playing = False
			return True
		return False
			
	def Next(self):
		if self.Send("n"):
			self._playing = True
			return True
		return False
			
		
	def Login(self, email, password):
		try:
			self._pianobar.expect_exact("Email:", timeout=1)
			self._pianobar.send(email+"\n")
			self._pianobar.expect_exact("Password:", timeout=1)
			self._pianobar.send(password+"\n")
			self._pianobar.expect_exact("Login... Ok.", timeout=5)
		except pexpect.ExceptionPexpect:
			return False
		return True
		
		
	def ListStations(self):
		stations = {}
		try:
			self._pianobar.send("s\b\n")
			self._pianobar.expect_exact("Select station:", timeout=1)
			for line in self._pianobar.before.splitlines():
				if re.search("\s+[0-9]+\)\s+", line) is not None: # match " #) "
					station_id = line[4:7].strip()
					station_name = line[13:].strip()
					stations[station_id] = station_name
		except pexpect.ExceptionPexpect:
			pass
		return stations
		
	def ChangeStation(self, station_id):
		try:
			self._pianobar.send("s\b")
			self._pianobar.send(str(station_id)+"\n")
			self._pianobar.expect_exact("Receiving new playlist... Ok", timeout=5)
			self._station = station_id
			self._playing = True
			return True
		except pexpect.ExceptionPexpect:
			return False
			
			
	def GetInfo(self):
		trackinfo = {}
		if self._station is not None:
			re_track = re.compile(".*\"(.+?)\" by \"(.+?)\" on \"(.+?)\".*", re.IGNORECASE)
			re_progress = re.compile("-([\:0-9]+)/([\:0-9]+)")
			try:
				self._pianobar.send("i\b")
				self._pianobar.expect_exact("Station", timeout=1)
				buffer = self.ExpectLines(4)
				for line in buffer.splitlines():
					# print line
					track = re_track.findall(line)
					if len(track) == 1 and len(track[0]) == 3:
						trackinfo = dict(trackinfo.items() + {"artist":track[0][1], "title":track[0][0], "album":track[0][2], "active":True, "playing":self._playing}.items())
					progress = re_progress.findall(line)
					if len(progress) == 1 and len(progress[0]) == 2:
						remaining = datetime.datetime.strptime(progress[0][0],"%M:%S")
						remaining = remaining.minute*60 + remaining.second
						length = datetime.datetime.strptime(progress[0][1],"%M:%S")
						length = length.minute*60 + length.second
						trackinfo = dict(trackinfo.items() + {"elapsed":(length-remaining), "length":length}.items())
			except pexpect.ExceptionPexpect:
				pass
		return trackinfo
		
	def GetPlaylist(self):
		playlist = []
		if self._station is not None:
			try:
				# Parse history
				self._pianobar.send("h\b\n")
				if self._pianobar.expect_exact(["No history yet","Select song:"], timeout=1) == 1:
					for line in self._pianobar.before.splitlines():
						if re.search("\s+[0-9]+\)\s+", line) is not None: # match " #) "
							track = line[9:].strip().split(" - ",1)
							if len(track) == 2:
								playlist.append({"artist":track[0], "title":track[1], "active":False, "playing":False})
				# Parse current
				current = self.GetInfo()
				playlist.append(self.GetInfo())
				# Parse upcoming
				self._pianobar.send("u\b")
				self._pianobar.expect("[\:0-9]+/[\:0-9]+", timeout=1)
				for line in self._pianobar.before.splitlines():
					if re.search("\s+[0-9]+\)\s+", line) is not None: # match " #) "
						track = line[9:].strip().split(" - ",1)
						if len(track) == 2:
							playlist.append({"artist":track[0], "title":track[1], "active":False, "playing":False})
			except pexpect.ExceptionPexpect:
				pass
		return playlist