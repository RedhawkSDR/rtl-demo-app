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

# This is a sample of a coroutine
    @gen.coroutine
    def get(self):
        http_client = AsyncHTTPClient()
        http_client.fetch("http://google.com",
			                callback=(yield gen.Callback("key")))
        response = yield gen.Wait("key")
        print response
        #do_something_with_response(response)
        self.write("template.html")

class RTLAppHandler(RequestHandler):
    def initialize(self, rtl_app):
        self.rtl_app = rtl_app

class SurveyHandler(RequestHandler):

    def get(self):
        yield gen.Task()
        self.write(dict(frequency=self.rtl_app.get_frequency(),
                        processing=self.rtl_app.get_processing())

    @gen.coroutine
    def post(self, frequency, processing):
        self.rtl_app.set_processing(frequency, processing)
        self.write(dict(frequency=rtl_app.get_frequency(),
                        processing=rtl_app.get_processing())


class DeviceHandler(RequestHandler): pass
class StatusHandler(RequestHandler): 
    def get(self):
        self.write({
          "url": "/survey",
          "data": {
          }
        })
        
class AudioWebSocketHandler(RequestHandler): pass

def get_application(rtl_app):
    application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": staticdir}),

    (r"/survey", SurveyHandler, dict(rtl_app=rtl_app)),
    (r"/device", DeviceHandler, dict(rtl_app=rtl_app)),
    (r"/output/audio", AudioWebSocketHandler, dict(rtl_app=rtl_app)),
    (r"/status", StatusHandler, dict(rtl_app=rtl_app))
], debug=options.debug)

    return application





if __name__ == '__main__':

    # parse the command line
    tornado.options.parse_command_line()
    application = get_application()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
