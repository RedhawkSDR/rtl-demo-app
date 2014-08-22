#!/usr/bin/env python

# system imports
import json
import os,sys
import logging

# third party imports
import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado import web
from tornado import gen

# application imports
import rtl_app

# setup command line options
from tornado.options import define, options

define("domain", default="REDHAWK", help="Redhawk domain")
define("port", default="8888", help="port")
define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")



# establish static directory from this module
staticdir = os.path.join(os.path.dirname(__import__(__name__).__file__), 'static')

class MainHandler(web.RequestHandler):

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

class _RTLAppHandler(web.RequestHandler):
    def initialize(self, rtl_app):
        self.rtl_app = rtl_app

class SurveyHandler(_RTLAppHandler):

    @gen.coroutine
    def _get_survey(self, callback=None):
        logging.info("start get survey")
        rtn = self.rtl_app.get_survey()
        logging.info("done get_suvery")
        return rtn

    @gen.coroutine
    def _set_survey(self, data, callback=None):
        logging.info("start set survey")
        rtn = self.rtl_app.set_survey(frequency=data['frequency'], demod=data['processing'])
        logging.info("done set_suvery")
        return rtn

    @gen.coroutine
    def _delete_survey(self, callback=None):
        logging.info("start delete survey")
        rtn = self.rtl_app.stop_survey()
        logging.info("done delete_suvery")
        return rtn


    @web.asynchronous
    @gen.coroutine
    def get(self):
        logging.debug("Survey GET")
        res = yield self._get_survey()
        self.write(dict(frequency=res['frequency'],
                        processing=res['demod']))

    @gen.coroutine
    def post(self):
        logging.debug("Survey POST")
        data = json.loads(self.request.body)
        try:
            res = yield self._set_survey(data)
            self.write(dict(success=True,
                            status=dict(frequency=res['frequency'],
                                        processing=res['demod'])))
        except rtl_app.BadFrequencyException:
            self.set_status(400)
            self.write(dict(success=False,
                            error='Frequency is invalid',
                            request=data))
        except rtl_app.BadDemodException:
            self.set_status(405)
            self.write(dict(success=False,
                            error="'%s' is not a valid processor" % data['processing'],
                            request=data))

        except Exception:
            logging.exception("Error setting survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=data))
        
    @gen.coroutine
    def delete(self):
        logging.debug("Survey POST")
        try:
            res = yield self._delete_survey()
            self.write(dict(success=True,
                            status=dict(frequency=res['frequency'],
                                        processing=res['demod'])))
        except Exception:
            logging.exception("Error stopping survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=data))


class DeviceHandler(_RTLAppHandler): pass
class StatusHandler(_RTLAppHandler): 
    def get(self):
        self.write({
          "url": "/survey",
          "data": {
          }
        })
        
class AudioWebSocketHandler(_RTLAppHandler): pass

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
    rtlapp = rtl_app.MockRTLApp(options.domain)
    application = get_application(rtlapp)
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
