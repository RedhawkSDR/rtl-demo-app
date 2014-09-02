#!/usr/bin/env python

# system imports
import unittest
import json
import logging

# tornado imports
import tornado
import tornado.testing
from tornado.testing import AsyncHTTPTestCase, LogTrapTestCase
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

# application imports
import server
import rtl_app
import mock_rtl_app

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

# NOTE: Use individual AyncHTTPClient requests, not self.http_client
#       because each http client contains the response.
#
#         AsyncHTTPClient(self.io_loop).fetch("http://www.tornadoweb.org/", self.stop)
#         response = self.wait()


class RESTfulTest(AsyncHTTPTestCase, LogTrapTestCase):

    # def setUp(self):
    #     super(RESTfulTest, self).setUp()
    #     rtl_app.RTLApp('REDHAWK_DEV').stop_survey()


    def get_app(self):
        # renewed each test case
        # self._mock_device = mock_rtl_app.MockRTLApp('REDHAWK_DEV')
        self._mock_device = rtl_app.RTLApp('REDHAWK_DEV')
        return server.get_application(self._mock_device, _ioloop=self.io_loop)

    # def stop(self, *args, **kwargs):
    #     print "STOPPING %s %s" % (args, kwargs)
    #     return super(RESTfulTest, self).stop(*args, **kwargs)
    # def get_new_ioloop(self):
        # return tornado.ioloop.IOLoop.instance()

    def test_survey_get(self):
        AsyncHTTPClient(self.io_loop).fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        # get the json reply
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['frequency'])
        self.assertEquals(None, data['processing'])

    def test_survey_post(self, pdata=dict(frequency=88500000, processing='fm')):
        # verify survey initial values
        self.test_survey_get()

        # update the survey
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url('/survey'), 'POST', 
                        body=json.dumps(pdata)),
                        self.stop)
        responsex = self.wait()

        # values should be identical
        self.assertEquals(200, responsex.code)
        data = json.loads(responsex.body)
        self.assertTrue(data['success'])
        self.assertEquals(pdata, data['status'])

        # getting the survey should be equal too
        AsyncHTTPClient(self.io_loop).fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(pdata, data)

    def test_survey_delete(self):

        pdata = dict(frequency=107500000, processing='fm')
        # run the post tests to set some values
        self.test_survey_post(pdata=pdata)

        # now stop the processing
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url('/survey'), 'DELETE'), 
                        self.stop)

        response = self.wait()

        # values should be identical
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(True, data['success'])
        self.assertEquals(None, data['status']['frequency'])
        self.assertEquals(None, data['status']['processing'])

        # getting the survey should be equal too
        AsyncHTTPClient(self.io_loop).fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['frequency'])
        self.assertEquals(None, data['processing'])

    def test_survey_post_bounds_errors(self):
        request = dict(frequency=10, processing='fm')
        # Frequency too low
        AsyncHTTPClient(self.io_loop).fetch(
            HTTPRequest(self.get_url('/survey'), 'POST', 
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
            HTTPRequest(self.get_url('/survey'), 'POST', 
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
            HTTPRequest(self.get_url('/survey'), 'POST', 
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
            HTTPRequest(self.get_url('/survey'), 'POST', 
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
        AsyncHTTPClient(self.io_loop).fetch(self.get_url('/device'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        # get the json reply
        data = json.loads(response.buffer.getvalue())
        self.assertEquals('rtl', data['type'])
        self.assertEquals('unavailable', data['status'])

        self._mock_device._set_device('rtl', 'ready')
        AsyncHTTPClient(self.io_loop).fetch(self.get_url('/device'), self.stop)
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

        AsyncHTTPClient(self.io_loop).fetch(self.get_url('/device'), self.stop)
        response = self.wait()
        self.assertEquals(500, response.code)
        # get the json reply
        data = json.loads(response.body)
        self.assertFalse(data['success'])
        self.assertEquals('An unknown system error occurred', data['error'])


if __name__ == '__main__':

   # logging.basicConfig(level=logging.debug)
    tornado.testing.main()
