#!/usr/bin/env python

# system imports
import unittest
import json
import logging

# tornado imports
import tornado.testing
from tornado.testing import AsyncHTTPTestCase, LogTrapTestCase
from tornado.httpclient import HTTPRequest

# application imports
import server
import rtl_app

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

class RESTfulTest(AsyncHTTPTestCase, LogTrapTestCase):

    def get_app(self):
        return server.get_application(rtl_app.MockRTLApp('REDHAWK_DEV'))

    def test_survey_get(self):
        self.http_client.fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        # get the json reply
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['frequency'])
        self.assertEquals(None, data['processing'])

        self.http_client.fetch(self.get_url('/survey'), self.stop)

    def test_survey_post(self, pdata=dict(frequency=88500000, processing='fm')):
        # verify survey initial values
        self.test_survey_get()

        # update the survey
        self.http_client.fetch(
            HTTPRequest(self.get_url('/survey'), 'POST', 
                        body=json.dumps(pdata)),
                        self.stop)
        response = self.wait()

        # values should be identical
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertTrue(data['success'])
        self.assertEquals(pdata, data['status'])

        # getting the survey should be equal too
        self.http_client.fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(pdata, data)

    def test_survey_delete(self):

        pdata = dict(frequency=107500000, processing='fm')
        # run the post tests to set some values
        self.test_survey_post(pdata=pdata)

        # now stop the processing
        self.http_client.fetch(
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
        self.http_client.fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['frequency'])
        self.assertEquals(None, data['processing'])

    def test_survey_post_errors(self):
        request = dict(frequency=10, processing='fm')
        # Frequency too low
        self.http_client.fetch(
            HTTPRequest(self.get_url('/survey'), 'POST', 
                        body=json.dumps(request)),
                        self.stop)
        response = self.wait()

        self.assertEquals(400, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertFalse(data['success'])
        self.assertEquals('Frequency is invalid', data['error'])
        self.assertEquals(request, data['request'])

        # frequency too high
        request = dict(frequency=10e20, processing='fm')
        self.http_client.fetch(
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
        self.http_client.fetch(
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


if __name__ == '__main__':

   # logging.basicConfig(level=logging.debug)
    tornado.testing.main()
