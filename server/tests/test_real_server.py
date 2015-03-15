#!/usr/bin/env python
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK rtl-demo-app.
#
# REDHAWK rtl-demo-app is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK rtl-demo-app is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

# system imports
import unittest
import json
import logging
import time
import threading
from functools import partial
from collections import namedtuple

# tornado imports
import tornado
import tornado.testing
from tornado.testing import AsyncHTTPTestCase, LogTrapTestCase
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado import websocket

# application imports
import server
from rtl_app import AsyncRTLApp

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

# NOTE: Use individual AyncHTTPClient requests, not self.http_client
#       because each http client contains the response.
#
#         AsyncHTTPClient(self.io_loop).fetch("http://www.tornadoweb.org/", self.stop)
#         response = self.wait()

class RealRESTfulTest(AsyncHTTPTestCase):

    # def setUp(self):
    #     super(RESTfulTest, self).setUp()
    #     rtl_app.RTLApp('REDHAWK_DEV').stop_survey()
    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        super(RealRESTfulTest, self).setUp()

    def get_app(self):
        # create a concurrent version of the applicaiton
        concurrent_rtl_class = AsyncRTLApp

        # application renewed each test case
        self._rtl_app = concurrent_rtl_class('REDHAWK_TEST')
        return server.get_application(self._rtl_app,
                                      _ioloop=self.io_loop)


    @tornado.testing.gen_test(timeout=60)
    def test_streaming_psk_float(self, url='/output/psk/float', bytes=1024):
        yield self._rtl_app.set_simulation(True)
        yield self._rtl_app.set_survey(101000000, 'fm')
        url = self.get_url(server._BASE_URL + url).replace('http', 'ws')
        conn1 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop)
        conn2 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop)
        for x in xrange(10):
            message = yield conn1.read_message()
            # This websocket doesn't distinquish between binary and text
            # so we will to convert to json.  If fails, binary!
            try:
                data = json.loads(message)
                print "Connection 1 message #%s: %s" % (x, message)
            except Exception, e:
                print e
                print "Connection 1 message #%s: %s bytes" % (x, len(message))
            # self.assertEquals(stat, data['body']['status'])

            # FIXME: assert SRI

            message = yield conn2.read_message()
            logging.debug("Connection 2 message #%s: %s", x, len(message))
            # logging.debug("Connection 2 message #%s: %s", x, message)
            # data = json.loads(message)
            # self.assertEquals(stat, data['body']['status'])
        conn1.close()
        conn2.close()        
        # FIXME: Ensure that close is being called on websocket so that is tested
        # tried with stop(), but unsure if that does anything
        self.stop()
        self.fail("Whatever")


        
    def test_streaming_psk_short(self):
        self.test_streaming_psk_float(url='/output/psk/short', bytes=416)

if __name__ == '__main__':

    # FIXME: Make command line arugment to replace rtl_app with mock
    #rtl_app = mock_rtl_app
   # logging.basicConfig(level=logging.debug)
    tornado.testing.main()

