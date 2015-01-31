import __builtin__
import cherrypy
from genshi.core import Markup
from genshi.template import TemplateLoader
import os
import threading

genshi = TemplateLoader(
    os.path.join(os.path.dirname(__file__),"public_html"),
    auto_reload=True
)

def Render(file, page):
	if page == None: page = {}
	global PlaybackModule
	if __builtin__.PlaybackModule == None:
		page["__PLAYING__"] = False
	else:
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
				
		if len(vpath) >= 1:
			return self.playback
		return vpath
		
	@cherrypy.expose
	def index(self):
		return Render("index.html", None)
		
class Playback(object):
	@cherrypy.expose
	def index(self):
		return "Playback"
		
		
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