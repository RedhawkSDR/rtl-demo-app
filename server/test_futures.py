#!/usr/bin/env python
from gevent import monkey; monkey.patch_all()

import unittest
import sys
import time
from tornado import gen
from tornado.testing import AsyncTestCase, LogTrapTestCase, main, gen_test
import rtl_app_wrapper
import gevent

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))


class FuturesTest(AsyncTestCase):

	@rtl_app_wrapper._wrap_background_func
	def _sleepfunc(self, input, duration=1, exception=False):
		print "RAN TEST!!!"
		time.sleep(duration)
		if exception:
			raise input
		print "TEST DONE"
		return input


	@gen_test
	def test_background_future(self):
		''' 
		    Runs a thread that sleeps in the background and generates a Future to indicate it's
		    done or raised an exception.
		'''
		f = yield self._sleepfunc("the input is 1", 1)
		print "The future is %s" %f
		# self.io_loop.add_future(f, self.stop)
		# print "RESULT IS '%s'" % self.wait()
		self.assertEquals("the input is 1", f)

	def test_background_future_exception(self):
		''' 
		    Runs a thread that sleeps in the background and generates a Future to indicate it's
		    done or raised an exception.
		'''
		f = self._sleepfunc(IndexError('whatever'), 1, exception=True)
		print "The future is %s" %f
		self.io_loop.add_future(f, self.stop)
		gevent.sleep(0)
		f2 = self.wait()
		# print "RESULT IS '%s'" % self.wait()
		self.assertEquals(IndexError, type(f2.exception()))

	@rtl_app_wrapper._wrap_background_func
	def _callbackfunc(self, input, duration=1, callback=None):
		print "input=%s, callback=%s" % (input, callback)
		def background(i):
			print "_callbackfunc!!!"
			time.sleep(duration)
			callback(i)
		gevent.spawn(background, input)

	@gen_test
	def test_callback_future(self):
		_cbfunc = rtl_app_wrapper._return_future_ioloop(self._callbackfunc)
		# import pdb
		# pdb.set_trace()
		f = yield _cbfunc("the input is 1", 1)
		print "The future is %s" %f
		# self.io_loop.add_future(f, self.stop)
		# print "RESULT IS '%s'" % self.wait()
		self.assertEquals("the input is 1", f)




if __name__ == '__main__':

    # FIXME: Make command line arugment to replace rtl_app with mock
    #rtl_app = mock_rtl_app
   # logging.basicConfig(level=logging.debug)
    main()
