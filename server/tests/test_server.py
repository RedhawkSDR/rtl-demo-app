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
from rtl_app import MockAsyncRTLApp

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

# NOTE: Use individual AyncHTTPClient requests, not self.http_client
#       because each http client contains the response.
#
#         AsyncHTTPClient(self.io_loop).fetch("http://www.tornadoweb.org/", self.stop)
#         response = self.wait()

class RESTfulTest(AsyncHTTPTestCase):

    # def setUp(self):
    #     super(RESTfulTest, self).setUp()
    #     rtl_app.RTLApp('REDHAWK_DEV').stop_survey()
    def setUp(self):
        logging.getLogger().setLevel(logging.DEBUG)
        super(RESTfulTest, self).setUp()

    def get_app(self):
        # create a concurrent version of the applicaiton
        concurrent_rtl_class = MockAsyncRTLApp
        #concurrent_rtl_class = rtl_app.AsyncRTLApp

        # application renewed each test case
        self._mock_device = concurrent_rtl_class('REDHAWK_DEV', delayfunc=lambda f: time.sleep(.1))

        #self._mock_device = rtl_app.RTLApp('REDHAWK_DEV')
        return server.get_application(self._mock_device,
                                      _ioloop=self.io_loop)


    def test_survey_get(self):
        AsyncHTTPClient(self.io_loop).fetch(self.get_url(server._BASE_URL + '/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        # get the json reply
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['status']['frequency'])
        self.assertEquals(None, data['status']['processing'])
        self.assertEquals(['fm'], data['availableProcessing'])

    def test_survey_post(self, pdata=dict(frequency=88500000, processing='fm')):
        # verify survey initial values
        self.test_survey_get()

        # update the survey
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url(server._BASE_URL + '/survey'), 'POST',
                        body=json.dumps(pdata)),
                        self.stop)
        responsex = self.wait()

        # values should be identical
        self.assertEquals(200, responsex.code)
        data = json.loads(responsex.body)
        self.assertTrue(data['success'])
        self.assertEquals(pdata, data['status'])

        # getting the survey should be equal too
        AsyncHTTPClient(self.io_loop).fetch(self.get_url(server._BASE_URL + '/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(pdata, data['status'])

    def test_survey_delete(self):

        pdata = dict(frequency=107500000, processing='fm')
        # run the post tests to set some values
        self.test_survey_post(pdata=pdata)

        # now stop the processing
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url(server._BASE_URL + '/survey'), 'DELETE'),
                        self.stop)

        response = self.wait()

        # values should be identical
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(True, data['success'])
        self.assertEquals(None, data['status']['frequency'])
        self.assertEquals(None, data['status']['processing'])

        # getting the survey should be equal too
        AsyncHTTPClient(self.io_loop).fetch(self.get_url(server._BASE_URL + '/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['status']['frequency'])
        self.assertEquals(None, data['status']['processing'])

    def test_survey_post_bounds_errors(self):
        request = dict(frequency=10, processing='fm')
        # Frequency too low
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url(server._BASE_URL + '/survey'), 'POST',
                        body=json.dumps(request)),
                        self.stop)
        response = self.wait()

        # print response, response.body
        self.assertEquals(400, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertFalse(data['success'])
        self.assertEquals('Frequency is invalid', data['error'])
        self.assertEquals(request, data['request'])

        # frequency too high
        request = dict(frequency=10e20, processing='fm')
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url(server._BASE_URL + '/survey'), 'POST',
                        body=json.dumps(request)),
                        self.stop)
        response = self.wait()

        # values should be identical
        self.assertEquals(400, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertFalse(data['success'])
        self.assertEquals('Frequency is invalid', data['error'])
        self.assertEquals(request, data['request'])

        # bad processor
        badprocessor = 'FKJFKDJFK'
        request = dict(frequency=99500000, processing=badprocessor)
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url(server._BASE_URL + '/survey'), 'POST',
                        body=json.dumps(request)),
                        self.stop)
        response = self.wait()

        # values should be identical
        self.assertEquals(405, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertFalse(data['success'])
        self.assertEquals("'%s' is not a valid processor" % badprocessor, data['error'])
        self.assertEquals(request, data['request'])

    def test_survey_post_json_errors(self):
        request = dict(frequency=10, processing='fm')
        # Frequency too low
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url(server._BASE_URL + '/survey'), 'POST',
                        body='this is not jsof:::$#'),
                        self.stop)
        response = self.wait()

        self.assertEquals(500, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertFalse(data['success'])
        self.assertEquals('this is not jsof:::$#', data['request'])
        self.assertEquals('An unknown system error occurred', data['error'])

        #FIXME: Add test case with bad fields
        #FIXME: Add test case with missing fields


    # fixme: does not work yet
    def test_device_get(self):
        AsyncHTTPClient(self.io_loop).fetch(self.get_url(server._BASE_URL + '/device'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        # get the json reply
        data = json.loads(response.buffer.getvalue())
        self.assertEquals('rtl', data['type'])
        self.assertEquals('unavailable', data['status'])

        self._mock_device._set_device('rtl', 'ready')
        AsyncHTTPClient(self.io_loop).fetch(self.get_url(server._BASE_URL + '/device'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        # get the json reply
        data = json.loads(response.buffer.getvalue())
        self.assertEquals('rtl', data['type'])
        self.assertEquals('ready', data['status'])

    def test_device_system_failure(self):
        def raisefunc(f):
            raise ValueError(f)

        # this causes the application to fail
        self._mock_device._delayfunc = raisefunc

        AsyncHTTPClient(self.io_loop).fetch(self.get_url(server._BASE_URL + '/device'), self.stop)
        response = self.wait()
        self.assertEquals(500, response.code)
        # get the json reply
        data = json.loads(response.body)
        self.assertFalse(data['success'])
        self.assertEquals('An unknown system error occurred', data['error'])


    @tornado.testing.gen_test
    def test_status_ws(self):

        _mock_device = self._mock_device
        class EventThread(threading.Thread):
            def run(self):
                for x in xrange(5):
                    stat = x % 2 and 'ready' or 'unavailable'
                    _mock_device._set_device('rtl', stat)
                    time.sleep(.2)
  
        url = self.get_url(server._BASE_URL + '/status').replace('http', 'ws')
        conn1 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop) 
        self.io_loop.add_callback(EventThread().start)
        for x in xrange(5):
            message = yield conn1.read_message()
            print "Message #%s: %s" % (x, message)
        conn1.protocol.close()
 
    @tornado.testing.gen_test
    def test_status_dual_ws(self):

        _mock_device = self._mock_device
        class EventThread(threading.Thread):
            def run(self):
                for x in xrange(5):
                    stat = x % 2 and 'ready' or 'unavailable'
                    _mock_device._set_device('rtl', stat)
                    time.sleep(.2)
  
        url = self.get_url(server._BASE_URL + '/status').replace('http', 'ws')
        conn1 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop) 
        conn2 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop) 
        self.io_loop.add_callback(EventThread().start)
        for x in xrange(5):
            stat = x % 2 and 'ready' or 'unavailable'
            message = yield conn1.read_message()
            logging.debug("Connection 1 message #%s: %s", x, message)
            data = json.loads(message)
            self.assertEquals(stat, data['body']['status'])

            message = yield conn2.read_message()
            logging.debug("Connection 2 message #%s: %s", x, message)
            data = json.loads(message)
            self.assertEquals(stat, data['body']['status'])
        conn1.close()
        conn2.close()
        # FIXME: Ensure that close is being called on websocket so that is tested
        # tried with stop(), but unsure if that does anything
        self.stop()

    @tornado.testing.gen_test
    def test_streaming_ws(self):
        SRI=namedtuple('SRI', 'hversion xstart xdelta xunits subsize ystart ydelta yunits mode streamID blocking keywords')

        _mock_device = self._mock_device
        class SRIThread(threading.Thread):
            def run(self):
                for x in xrange(5):
                    _mock_device._post_SRI(_mock_device.PORT_TYPE_WIDEBAND, 
                        SRI(hversion='5',
                             xstart=1,
                             xdelta=2,
                             xunits=3,
                             subsize=25,
                             ystart=3,
                             ydelta=2,
                             yunits=45,
                             mode='big',
                             streamID='streamid',
                             blocking=False, 
                             keywords=[]))
                    time.sleep(.1)

        class DataThread(threading.Thread):
            def run(self):
                for x in xrange(5):
                    _mock_device._post_packet(_mock_device.PORT_TYPE_WIDEBAND, [1, 2, 3, 4], 0, False, 'foo')
                    time.sleep(.2)
  
        print "TESTING"
        url = self.get_url(server._BASE_URL + '/output/psd/wideband').replace('http', 'ws')
        conn1 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop) 
        conn2 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop) 
        self.io_loop.add_callback(SRIThread().start)
        self.io_loop.add_callback(DataThread().start)
        for x in xrange(10):
            message = yield conn1.read_message()
            logging.error("Connection 1 message #%s: %s", x, message)
            # data = json.loads(message)
            # self.assertEquals(stat, data['body']['status'])

            # FIXME: assert SRI

            message = yield conn2.read_message()
            logging.debug("Connection 2 message #%s: %s", x, message)
            # logging.debug("Connection 2 message #%s: %s", x, message)
            # data = json.loads(message)
            # self.assertEquals(stat, data['body']['status'])
        conn1.close()
        conn2.close()
        # FIXME: Ensure that close is being called on websocket so that is tested
        # tried with stop(), but unsure if that does anything
        self.stop()


    @tornado.testing.gen_test
    def test_streaming_psk_float(self):
        SRI=namedtuple('SRI', 'hversion xstart xdelta xunits subsize ystart ydelta yunits mode streamID blocking keywords')

        _mock_device = self._mock_device
        class SRIThread(threading.Thread):
            def run(self):
                for x in xrange(1):
                    _mock_device._post_SRI(_mock_device.PORT_TYPE_PSK_FLOAT,
                                           SRI(hversion='1',
                                               xstart=0.0,
                                               xdelta=8.421052631578948e-4,
                                               xunits=1,
                                               subsize=0,
                                               ystart=0,
                                               ydelta=0.0,
                                               yunits=0,
                                               mode='scalar',
                                               streamID='MyStreamID',
                                               blocking=False,
                                               keywords={'CHAN_RF': 100085748,
                                               'COL_RF': 1.000999984741211e8}))
                    time.sleep(.1)

        class DataThread(threading.Thread):
            def run(self):
                for x in xrange(5):
                    _mock_device._post_packet(_mock_device.PORT_TYPE_WIDEBAND, [1, 2, 3, 4], 0, False, 'foo')
                    time.sleep(.2)

        print "TESTING"
        url = self.get_url(server._BASE_URL + '/output/psd/wideband').replace('http', 'ws')
        conn1 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop)
        conn2 = yield websocket.websocket_connect(url,
                                                  io_loop=self.io_loop)
        self.io_loop.add_callback(SRIThread().start)
        self.io_loop.add_callback(DataThread().start)
        for x in xrange(10):
            message = yield conn1.read_message()
            logging.error("Connection 1 message #%s: %s", x, message)
            # data = json.loads(message)
            # self.assertEquals(stat, data['body']['status'])

            # FIXME: assert SRI

            message = yield conn2.read_message()
            logging.debug("Connection 2 message #%s: %s", x, message)
            # logging.debug("Connection 2 message #%s: %s", x, message)
            # data = json.loads(message)
            # self.assertEquals(stat, data['body']['status'])
        conn1.close()
        conn2.close()
        # FIXME: Ensure that close is being called on websocket so that is tested
        # tried with stop(), but unsure if that does anything
        self.stop()
if __name__ == '__main__':

    # FIXME: Make command line arugment to replace rtl_app with mock
    #rtl_app = mock_rtl_app
   # logging.basicConfig(level=logging.debug)
    tornado.testing.main()

