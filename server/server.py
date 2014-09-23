#!/usr/bin/env python

# do this as early as possible in your application
from gevent import monkey; monkey.patch_all()

# system imports
import json
import os,sys
import logging
import time
import functools
import numpy

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
from rtl_app import AsyncRTLApp
from _common import BadDemodException, BadFrequencyException

# setup command line options
from tornado.options import define, options

define("domain", default="REDHAWK_DEV", help="Redhawk domain")
define("port", default="8888", help="port")
define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")


# establish static directory from this module
staticdir = os.path.join(os.path.dirname(__import__(__name__).__file__), 'static')


def _floats2bin(flist):
    """
        Converts a list of python floating point values
        to a packed array of IEEE 754 32 bit floating point
    """
    return numpy.array(flist).astype('float32').tostring()


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

            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
                                        processing=survey['demod']),
                            availableProcessing=processing))

        # FIXME: 
        except StandardError, e:
            # unable to find domain
            self.write(dict(success=True,
                            status=dict(frequency=None,
                                        processing=None),
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

    def initialize(self, rtl_app, _ioloop=None):
        self.rtl_app = rtl_app

        # explicit ioloop for unit testing
        if not _ioloop:
            _ioloop = ioloop.IOLoop.instance()

        self.ioloop = _ioloop

    def open(self):
        logging.debug('Event handler open')
        # register event handling
        self.rtl_app.add_event_listener(self._post_event)

    def on_message(self, message):
        logging.debug('stream message[%d]: %s', len(message), message)

    def on_close(self):
        logging.debug('Stream CLOSE')
        self.rtl_app.rm_event_listener(self._post_event)

    def _post_event(self, event):
        # if connection still open, post the next event
        #if self.ws_connection:
        self.ioloop.add_callback(self.write_message, event)
    

class PSDHandler(websocket.WebSocketHandler):

    def initialize(self, rtl_app, port_type, _ioloop=None):
        self.rtl_app = rtl_app
        self.port_type = port_type

        # explicit ioloop for unit testing
        if not _ioloop:
            _ioloop = ioloop.IOLoop.instance()

        self._ioloop = _ioloop

    def open(self, ):
        logging.debug('PSD handler for %s open', self.port_type)
        # register event handling
        self.rtl_app.add_stream_listener(self.port_type, self._pushPacket, self._pushSRI)

    def on_message(self, message):
        logging.debug('stream message[%d]: %s', len(message), message)

    def on_close(self):
        logging.debug('PSD handler stream CLOSE')
        try:
            self.rtl_app.rm_stream_listener(self.port_type, self._pushPacket, self._pushSRI)
        except Exception, e:
            logging.exception('Error disconnecting port %s' % self.port_type)

    def _pushSRI(self, SRI):
        self._ioloop.add_callback(self.write_message, 
            dict(hversion=SRI.hversion,
                xstart=SRI.xstart,
                xdelta=SRI.xdelta,
                xunits=SRI.xunits,
                subsize=SRI.subsize,
                ystart=SRI.ystart,
                ydelta=SRI.ydelta,
                yunits=SRI.yunits,
                mode=SRI.mode,
                streamID=SRI.streamID,
                blocking=SRI.blocking,
                keywords=dict(((kw.id, kw.value.value()) for kw in SRI.keywords))))

    def _pushPacket(self, data, ts, EOS, stream_id):

        # FIXME: need to write ts, EOS and stream id
        self._ioloop.add_callback(self.write_message, _floats2bin(data), binary=True)

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(PSDHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')

def get_application(rtl_app, _ioloop=None):
    application = tornado.web.Application([
    (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": staticdir}),

    (r"/survey", SurveyHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    (r"/device", DeviceHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
#    (r"/output/audio", AudioWebSocketHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    # (r"/status", StatusHandler, dict(rtl_app=rtl_app, ioloop=_ioloop))
    (r"/status", EventHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
    (r"/output/psd/narrowband", PSDHandler,
     dict(rtl_app=rtl_app, port_type=rtl_app.PORT_TYPE_NARROWBAND, _ioloop=_ioloop)),
    (r"/output/psd/wideband", PSDHandler,
     dict(rtl_app=rtl_app, port_type=rtl_app.PORT_TYPE_WIDEBAND, _ioloop=_ioloop))
], debug=options.debug)

    return application





if __name__ == '__main__':

    # parse the command line
    define("mock", default=False, type=bool, help="Run with the mock application back end")
    define("delay", default=0, type=int, help="Mock delay in milliseconds")
    define("rtlstat", default=None, type=str, help="Program that returns RTL device status using a successful exit code. 0=ready, 1=not ready")
    tornado.options.parse_command_line()
    if options.mock:
        from mock_rtl_app import AsyncRTLApp
        rtlapp = AsyncRTLApp(options.domain, 
                                    delayfunc=lambda f: time.sleep(options.delay))
    else:
        rtlapp = AsyncRTLApp(options.domain, 
                        delayfunc=lambda f: time.sleep(options.delay),
                        rtlstatprog=options.rtlstat)
    application = get_application(rtlapp)
    application.listen(options.port)
    ioloop.IOLoop.instance().start()
