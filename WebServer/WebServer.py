import __builtin__
import cherrypy
from genshi.core import Markup
from genshi.template import TemplateLoader
import json
import os
import threading
import time

# Set public_html as the root HTTP folder
genshi = TemplateLoader(
    os.path.join(os.path.dirname(__file__), "public_html"),
    auto_reload = True
)

def Render(file, page):
	if page == None: page = {}
	
	# Get PlaybackModule status
	global PlaybackModule
	page["__STATUS__"] = __builtin__.Status
	
	# Render child template, set output in "page"
	child = genshi.load(file)
	page["__PAGE__"] = Markup(child.generate(page=page).render())
	
	# Render parent template, return output
	parent = genshi.load("public_html.html")
	return parent.generate(page=page).render("html", doctype="html")
	

class Cherry(object):
	def __init__(self):
		self.playback = Playback()
		
	def _cp_dispatch(self, vpath):
		# lower() everything in the path except the last piece (could contain params?)
		if len(vpath) >= 1:
			for index, path in enumerate(vpath[:-1]):
				vpath[index] = path.lower()
				
		# /playback/*
		if len(vpath) == 2 and vpath[0] == 'playback':
			return self.playback
			
		return vpath
		
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['GET'])
	def index(self):
		return Render("index.html", None)
		
	# GET Comet (JavaScript.EventSource) handler/streamer
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['GET'])
	def status(self):
		cherrypy.response.headers['Content-Type'] = 'text/event-stream'
		def run():
			timer_ping = time.time()
			status_curr = None
			while not __builtin__.Shutdown.isSet():
				# 'ping' - send small pings so CherryPy can track timeouts/disconnects
				if (timer_ping + 5) <= time.time():
					yield 'event: ping\n'+'data: {}\n'+'\n'
				# 'status' - update playback/internet status
				status_new = json.dumps(__builtin__.Status)
				if status_new != status_curr:
					yield 'event: status\n'+'data: '+status_new+'\n\n'
					status_curr = status_new
				time.sleep(0.1)
		return run()
	status._cp_config = {'response.stream': True, 'response.timeout': 30}
		
class Playback(object):
	# GET JSON PlaybackModule status
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['GET'])
	@cherrypy.tools.json_out()
	def status(self):
		return __builtin__.Status
		
	# POST PlaybackModule play
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def play(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Play()
		return self.status()
		
	# POST PlaybackModule pause
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def pause(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Pause()
		return self.status()
		
	# POST PlaybackModule previous
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def prev(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Prev()
		return self.status()
		
	# POST PlaybackModule next
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def next(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Next()
		return self.status()
		
		
class Server(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
	def run(self):
		# Setup CherryPy server and start
		cherrypy.config.update("CherryPy.conf")
		cherrypy_conf = {"/static":{
			"tools.staticdir.on": True,
			"tools.staticdir.dir": os.path.join(os.path.dirname(__file__),"public_html/static")
		}}
		cherrypy.quickstart(Cherry(), "/", cherrypy_conf)
	def stop(self):
		# Stop CherryPy server
		cherrypy.engine.exit()