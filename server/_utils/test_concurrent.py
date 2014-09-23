#!/usr/bin/env python
from gevent import monkey; monkey.patch_all()

import unittest
import sys
import logging
import time

import gevent
from tornado import gen
from tornado.testing import AsyncTestCase, LogTrapTestCase, main, gen_test


import concurrent

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))


class FuturesTest(AsyncTestCase):

	@concurrent.background_task
	def _sleepfunc(self, input, duration=1, exception=False):
		logging.debug("_sleepfun start")
		time.sleep(duration)
		if exception:
			raise input
		logging.debug("_sleepfun end")
		return input


	@gen_test
	def test_background_future(self):
		''' 
		    Runs a thread that sleeps in the background and generates a Future to indicate it's
		    done or raised an exception.
		'''
		f = yield self._sleepfunc("the input is 1", 1)
		logging.debug("The future is %s", f)
		self.assertEquals("the input is 1", f)

	@gen_test
	def test_background_future_except1(self):
		''' 
		    Runs a thread that sleeps in the background and generates a Future to indicate it's
		    done or raised an exception.
		'''
		try:
			f = yield self._sleepfunc(ValueError('ignore me'), 1, exception=True)
			self.fail("Expecting ValueError")
		except ValueError:
			logging.info("Manual inspection of stack trace required:", exc_info=1)

	def test_background_future_exception(self):
		''' 
		    Runs a thread that sleeps in the background and generates a Future to indicate it's
		    done or raised an exception.
		'''
		f = self._sleepfunc(ValueError('ignore me'), 1, exception=True)
		logging.debug("The future is %s", f)
		self.io_loop.add_future(f, self.stop)
		gevent.sleep(0)
		f2 = self.wait()
		# print "RESULT IS '%s'" % self.wait()
		self.assertEquals(ValueError, type(f2.exception()))


	@gen_test
	def test_callback_future(self):

		@concurrent.safe_return_future
		def cbfunc(input, duration=1, callback=None):
			logging.debug("input=%s, callback=%s", input, callback)
			def background(i):
				logging.debug("invoking cbfunc")
				time.sleep(duration)
				callback(i)
			gevent.spawn(background, input)

		f = yield cbfunc("the input is 1", 1)
		logging.debug("The future is %s", f)
		self.assertEquals("the input is 1", f)


	#TODO: Add tests for callback options


if __name__ == '__main__':

	# to enable logging, use --logging=debug
    main()