import __builtin__
import cherrypy
from genshi.core import Markup
from genshi.template import TemplateLoader
import json
import os
import threading
import time

genshi = TemplateLoader(
    os.path.join(os.path.dirname(__file__),"public_html"),
    auto_reload=True
)

def Render(file, page):
	if page == None: page = {}
	global PlaybackModule
	page["__PLAYING__"] = __builtin__.PlaybackModule.IsPlaying()
	
	child = genshi.load(file)
	page["__PAGE__"] = Markup(child.generate(page=page).render())
	
	parent = genshi.load("public_html.html")
	return parent.generate(page=page).render("html", doctype="html")
	

class Cherry(object):
	def __init__(self):
		self.playback = Playback()
		
	def _cp_dispatch(self, vpath):
		# lower() everything in the path except the last piece (could contain params)
		if len(vpath) >= 1:
			for index, path in enumerate(vpath[:-1]):
				vpath[index] = path.lower()
				
		if len(vpath) == 2 and vpath[0] == 'playback':
			return self.playback
			
		return vpath
		
	@cherrypy.expose
	def index(self):
		return Render("index.html", None)
		
class Playback(object):
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['GET'])
	def comet(self):
		cherrypy.response.headers['Content-Type'] = 'text/event-stream'
		def run():
			playback_status = None
			while True:
				playback_status_new = self.status()
				if playback_status_new != playback_status:
					playback_status = playback_status_new
					yield 'event: status\n'+'data: '+json.dumps(playback_status)+'\n\n'
				time.sleep(0.1)
		return run()
	comet._cp_config = {'response.stream': True}
	
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['GET'])
	@cherrypy.tools.json_out()
	def status(self):
		return {
			'__PLAYING__': __builtin__.PlaybackModule.IsPlaying()
		}
		
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def play(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Play()
		return self.status()
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def pause(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Pause()
		return self.status()
	@cherrypy.expose
	@cherrypy.tools.allow(methods=['POST'])
	@cherrypy.tools.json_out()
	def prev(self):
		if __builtin__.PlaybackModule != None:
			__builtin__.PlaybackModule.Prev()
		return self.status()
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
		cherrypy.config.update("CherryPy.conf")
		cherrypy_conf = {"/static":{
			"tools.staticdir.on": True,
			"tools.staticdir.dir": os.path.join(os.path.dirname(__file__),"public_html/static")
		}}
		cherrypy.quickstart(Cherry(), "/", cherrypy_conf)
		cherrypy.engine.block()
	def stop(self):
		cherrypy.engine.exit()