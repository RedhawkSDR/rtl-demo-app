#!/usr/bin/env python

# do this as early as possible in your application
from gevent import monkey; monkey.patch_all()

# system imports
import json
import os,sys
import logging
import time
import functools

# third party imports
import tornado
from tornado import ioloop
from tornado.httpclient import AsyncHTTPClient
from tornado import web
from tornado import websocket
from tornado import gen
import gevent
import threading

# application imports
import rtl_app
import rtl_app_wrapper
from _common import BadDemodException, BadFrequencyException

# setup command line options
from tornado.options import define, options

define("domain", default="REDHAWK_DEV", help="Redhawk domain")
define("port", default="8888", help="port")
define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")


# establish static directory from this module
staticdir = os.path.join(os.path.dirname(__import__(__name__).__file__), 'static')


class _RTLAppHandler(web.RequestHandler):
    def initialize(self, rtl_app, ioloop=None):
        self.rtl_app = rtl_app
        # explicit ioloop for unit testing
        self.ioloop = ioloop

class SurveyHandler(_RTLAppHandler):

    @gen.coroutine
    def get(self):
        logging.info("Survey GET")
        try:
            processing = self.rtl_app.get_available_processing()
            survey = yield self.rtl_app.get_survey()

            self.write(dict(status=dict(frequency=survey['frequency'],
                                        processing=survey['demod']),
                            availableProcessing=processing))
        except Exception:
            logging.exception("Error getting survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=self.request.body))

    @gen.coroutine
    def post(self):
        logging.debug("Survey POST")
        try:
            data = json.loads(self.request.body)
        except Exception:
            logging.exception('Unable to parse json: "%s"', self.request.body),
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=self.request.body))
            return


        try:
            survey = yield self.rtl_app.set_survey(frequency=data['frequency'], 
                                                   demod=data['processing'])
            logging.info("post CALLBACK")
            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
                                        processing=survey['demod'])))
        except BadFrequencyException:
            self.set_status(400)
            self.write(dict(success=False,
                            error='Frequency is invalid',
                            request=data))
        except BadDemodException:
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
        logging.info("Survey DELETE")
        try:
            survey = yield self.rtl_app.stop_survey()
            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
                                        processing=survey['demod'])))
        except Exception:
            logging.exception("Error stopping survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred'))

        logging.info("Survey DELETE End")


class DeviceHandler(_RTLAppHandler):

    @gen.coroutine
    def get(self):
        logging.info("Device GET")
        try:
            device = yield self.rtl_app.get_device()
            self.write(device)
        except Exception:
            logging.exception("Error getting device")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred'))
        logging.info("Survey DELETE End")


class StatusHandler(_RTLAppHandler): 
    def get(self):
        self.write({
          "url": "/survey",
          "data": {
          }
        })

class EventHandler(websocket.WebSocketHandler):

    def initialize(self, rtl_app, ioloop=None):
        self.rtl_app = rtl_app

        # explicit ioloop for unit testing
        if not ioloop:
            ioloop = ioloop.IOLoop.instance()

        self.ioloop = ioloop

    def open(self):
        logging.debug('Event handler open')
        # register event handling
        self._next_event(None)

    def on_message(self, message):
        logging.debug('stream message[%d]: %s', len(message), message)

    def on_close(self):
        logging.debug('Stream CLOSE')
        self.thread.stop()
        self.thread = None

    def _next_event(self, event_future):
        # if connection still open, get the next event
        if self.ws_connection:
            self.ioloop.add_future(self.rtl_app.next_event(), self._next_event)

        # if we got a future, write it
        if event_future:
            self.write_message(event_future.result())
    

def get_application(rtl_app, _ioloop=None):
    application = tornado.web.Application([
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": staticdir}),

    (r"/survey", SurveyHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    (r"/device", DeviceHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
#    (r"/output/audio", AudioWebSocketHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    # (r"/status", StatusHandler, dict(rtl_app=rtl_app, ioloop=_ioloop))
    (r"/status", EventHandler, dict(rtl_app=rtl_app, ioloop=_ioloop))
], debug=options.debug)

    return application





if __name__ == '__main__':

    # parse the command line
    define("mock", default=False, type=bool, help="Run with the mock application back end")
    define("delay", default=0, type=int, help="Mock delay in milliseconds")
    define("rtlstat", default=None, type=str, help="Program that returns RTL device status using a successful exit code. 0=ready, 1=not ready")
    tornado.options.parse_command_line()
    if options.mock:
        from mock_rtl_app import RTLApp
        rtlapp = RTLApp(options.domain, 
                                    delayfunc=lambda f: time.sleep(options.delay))
    else:
        rtlapp = rtl_app.RTLApp(options.domain, 
                                    delayfunc=lambda f: time.sleep(options.delay),
                                    rtlstatprog=options.rtlstat)
    application = get_application(rtlapp)
    application.listen(options.port)
    ioloop.IOLoop.instance().start()
