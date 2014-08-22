#!/usr/bin/env python

import unittest
from mockito import mock, verify
import tornado.testing
from tornado.testing import AsyncHTTPTestCase, LogTrapTestCase
from tornado.httpclient import HTTPRequest
import server
import rtl_app
import json
import logging

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

class RESTfulTest(AsyncHTTPTestCase, LogTrapTestCase):

    def get_app(self):
        return server.get_application(rtl_app.MockRTLApp('REDHAWK_DEV'))

    def test_survey_get(self):
        # The following two lines are equivalent to
        #   response = self.fetch('/')
        # but are shown in full here to demonstrate explicit use
        # of self.stop and self.wait.
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
        self.assertEquals(pdata, data)

        # getting the survey should be equal too
        self.http_client.fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        self.assertEquals(pdata, data)

    def test_survey_delete(self):

        pdata = dict(frequency=107500000, processing='fm')
        # run the post tests
        self.test_survey_post(pdata=pdata)

        self.http_client.fetch(
            HTTPRequest(self.get_url('/survey'), 'DELETE'), 
                        self.stop)

        response = self.wait()

        # values should be identical
        self.assertEquals(200, response.code)
        data = json.loads(response.buffer.getvalue())
        self.assertEquals(None, data['frequency'])
        self.assertEquals(None, data['processing'])

        # getting the survey should be equal too
        self.http_client.fetch(self.get_url('/survey'), self.stop)
        response = self.wait()
        self.assertEquals(200, response.code)
        self.assertEquals(None, data['frequency'])
        self.assertEquals(None, data['processing'])

if __name__ == '__main__':

   # logging.basicConfig(level=logging.debug)
    tornado.testing.main()
