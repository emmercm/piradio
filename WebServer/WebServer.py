import cherrypy
from genshi.core import Markup
from genshi.template import TemplateLoader
import os
import threading

genshi = TemplateLoader(
    os.path.join(os.path.dirname(__file__), "public_html"),
    auto_reload=True
)

def Render(file, page):
	if page == None:
		page = {}
	child = genshi.load(file)
	page["__CHILD__"] = Markup(child.generate(page=page).render())
	parent = genshi.load("public_html.html")
	return parent.generate(page=page).render("html", doctype="html")
	

class Cherry(object):
	def __init__(self):
		self.playback = Playback()
		
	def _cp_dispatch(self, vpath):
		if len(vpath) == 1:
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
		cherrypy.quickstart(Cherry(), "/", "CherryPy.conf")
		cherrypy.engine.block()
	def stop(self):
		cherrypy.engine.exit()