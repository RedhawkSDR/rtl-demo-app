#!/usr/bin/env python

import unittest
from mockito import mock, verify
import tornado.testing
from tornado.testing import AsyncHTTPTestCase, LogTrapTestCase
import server

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

class MyHTTPTest(AsyncHTTPTestCase, LogTrapTestCase):

    def get_app(self):
        return server.get_application()

    def test_homepage(self):
        # The following two lines are equivalent to
        #   response = self.fetch('/')
        # but are shown in full here to demonstrate explicit use
        # of self.stop and self.wait.
        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()
        # test contents of response

if __name__ == '__main__':
    tornado.testing.main()
