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

import unittest
import sys
import logging
import time

from tornado import gen
from tornado.testing import AsyncTestCase, LogTrapTestCase, main, gen_test

from futures import ThreadPoolExecutor

import tasking

EXECUTOR = ThreadPoolExecutor(4)

# all method returning suite is required by tornado.testing.main()
def all():
   return unittest.TestLoader().loadTestsFromModule(__import__(__name__))


class FuturesTest(AsyncTestCase):

	@tasking.background_task
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
		f2 = self.wait()
		# print "RESULT IS '%s'" % self.wait()
		self.assertEquals(ValueError, type(f2.exception()))


	@gen_test
	def test_callback_future(self):

		@tasking.safe_return_future
		def cbfunc(input, duration=1, callback=None):
			logging.debug("input=%s, callback=%s", input, callback)
			def background(i):
				logging.debug("invoking cbfunc")
				time.sleep(duration)
				callback(i)
			EXECUTOR.submit(background, input)

		f = yield cbfunc("the input is 1", 1)
		logging.debug("The future is %s", f)
		self.assertEquals("the input is 1", f)


	#TODO: Add tests for callback options


if __name__ == '__main__':

	# to enable logging, use --logging=debug
    main()
