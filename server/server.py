#!/usr/bin/env python

import json
import os,sys

import tornado.ioloop
import tornado.web
from tornado.web import RequestHandler
from tornado.httpclient import AsyncHTTPClient
from tornado import gen

# setup command line options
from tornado.options import define, options

define("domain", default="REDHAWK", help="Redhawk domain")
define("port", default="8888", help="port")
define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")



# establish static directory from this module
staticdir = os.path.join(os.path.dirname(__import__(__name__).__file__), 'static')

class MainHandler(RequestHandler):

    @gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        http_client.fetch("http://google.com",
			                callback=(yield gen.Callback("key")))
        response = yield gen.Wait("key")
        print response
        #do_something_with_response(response)
        self.write("template.html")

class SurveyHandler(RequestHandler): pass
class DeviceHandler(RequestHandler): pass
class StatusHandler(RequestHandler): 
    def get(self):
        self.write({
          "url": "/survey",
          "data": {
          }
        })
        
class AudioWebSocketHandler(RequestHandler): pass

def get_application():
    application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": staticdir}),

    (r"/survey", SurveyHandler),
    (r"/device", DeviceHandler),
    (r"/output/audio", AudioWebSocketHandler),
    (r"/status", StatusHandler)
], debug=options.debug)

    return application





if __name__ == '__main__':

    # parse the command line
    tornado.options.parse_command_line()
    application = get_application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
