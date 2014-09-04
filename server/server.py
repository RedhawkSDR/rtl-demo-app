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
from tornado import gen
import gevent
import threading

# application imports
import rtl_app
from _common import BadDemodException, BadFrequencyException

# setup command line options
from tornado.options import define, options

define("domain", default="REDHAWK_DEV", help="Redhawk domain")
define("port", default="8888", help="port")
define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")



# establish static directory from this module
staticdir = os.path.join(os.path.dirname(__import__(__name__).__file__), 'static')

def _exec_background(func, *args, **kwargs):
    '''
        Executes a function in a Greenlet thread
        then involes the callback on the ioloop when done.

        Callback is a required argument
    '''
    callback = kwargs.pop('callback')

    # use explicit ioloop for unit testing
    # Ref: https://github.com/tornadoweb/tornado/issues/663
    io_loop = kwargs.pop('ioloop', None)
    if not io_loop:
        io_loop = ioloop.IOLoop.instance()


    def _do_task(*args, **kwargs):
        rtn, error = None, None
        try:
            rtn = func(*args, **kwargs)
        except Exception, e:
            logging.exception("Callback exception")
            error = e

        io_loop.add_callback(callback, rtn, error)

    gevent.spawn(_do_task, *args, **kwargs)

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
    def initialize(self, rtl_app, ioloop=None):
        self.rtl_app = rtl_app
        # explicit ioloop for unit testing
        self.ioloop = ioloop

class SurveyHandler(_RTLAppHandler):


    @web.asynchronous
    def get(self):
        logging.info("Survey GET")
        def func():
            return self.rtl_app.get_survey(), self.rtl_app.get_available_processing()

        def cb(rtn, error):
            try:
                if error:
                    raise error
                self.write(dict(status=dict(frequency=rtn[0]['frequency'],
                                            processing=rtn[0]['demod']),
                                availableProcessing=rtn[1]))
            except Exception:
                logging.exception("Error getting survey")
                self.set_status(500)
                self.write(dict(success=False,
                                error='An unknown system error occurred',
                                request=self.request.body))

            self.finish()

        _exec_background(func, callback=cb, ioloop=self.ioloop)

    @web.asynchronous
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
            self.finish()
            return


        def task(data):
            return self.rtl_app.set_survey(frequency=data['frequency'], demod=data['processing'], timeout=5)


        def cb2(rtn, error):
            try:
                if error:
                    print type(error)
                    raise error
                logging.info("post CALLBACK")
                self.write(dict(success=True,
                                status=dict(frequency=rtn['frequency'],
                                            processing=rtn['demod'])))
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

            self.finish()
            logging.info("post CALLBACK completed")

        _exec_background(task, data, callback=cb2, ioloop=self.ioloop)

    @web.asynchronous
    def delete(self):
        logging.info("Survey DELETE")
        def task():
            return self.rtl_app.stop_survey()

        def callback(data, error):
            try:
                if error:
                    raise error
                
                self.write(dict(success=True,
                                status=dict(frequency=data['frequency'],
                                            processing=data['demod'])))
            except Exception:
                logging.exception("Error stopping survey")
                self.set_status(500)
                self.write(dict(success=False,
                                error='An unknown system error occurred'))

            self.finish()
            logging.info("Survey DELETE End")

        _exec_background(task, callback=callback, ioloop=self.ioloop)

class DeviceHandler(_RTLAppHandler):
    @web.asynchronous
    def get(self):
        logging.info("Device GET")
        def task():
            return self.rtl_app.get_device()

        def callback(data, error):
            try:
                if error:
                    raise error
                
                self.write(data)                
            except Exception:
                logging.exception("Error getting device")
                self.set_status(500)
                self.write(dict(success=False,
                                error='An unknown system error occurred'))

            self.finish()
            logging.info("Survey DELETE End")

        _exec_background(task, callback=callback, ioloop=self.ioloop)


class StatusHandler(_RTLAppHandler): 
    def get(self):
        self.write({
          "url": "/survey",
          "data": {
          }
        })
        
class AudioWebSocketHandler(_RTLAppHandler): pass

def get_application(rtl_app, _ioloop=None):
    application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": staticdir}),

    (r"/survey", SurveyHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    (r"/device", DeviceHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    (r"/output/audio", AudioWebSocketHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    (r"/status", StatusHandler, dict(rtl_app=rtl_app, ioloop=_ioloop))
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
