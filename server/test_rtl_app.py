#!/usr/bin/env python
import unittest
import sys
import rtl_app
import time
import collections
from tornado import gen
import logging
import os
from subprocess import Popen, PIPE

class RTLAppTest(unittest.TestCase):

	def setUp(self):
		# clear the running waveform before tests
		self.rtl_app = rtl_app.RTLApp("REDHAWK_DEV")
		self.rtl_app.stop_survey()

	def tearDown(self):
		# clear the running waveform before tests
		self.rtl_app.stop_survey()

	def test_halt(self, rtl=None):
		rtl = self.rtl_app

		for x in xrange(8):		
			a = rtl.set_survey(frequency=101100000, demod='fm')
			self.assertEquals(101100000, a['frequency'])
			self.assertEquals('fm', a['demod'])

			a = rtl.stop_survey()
			self.assertEquals(None, a['frequency'])
			self.assertEquals(None, a['demod'])
			print "SLEEPING"
			time.sleep(.5)




	def test_survey(self):		
		rtl = self.rtl_app


		events = collections.deque()
		def elisten(event):
			events.append(event)
		rtl.add_event_listener(elisten)

		a = rtl.get_survey()
		self.assertEquals(None, a['frequency'])
		self.assertEquals(None, a['demod'])
		a = rtl.set_survey(frequency=101100000, demod='fm')
		self.assertEquals('fm', a['demod'])
		self.assertEquals(101100000, a['frequency'])
		a = rtl.get_survey()
		self.assertEquals('fm', a['demod'])
		self.assertEquals(101100000, a['frequency'])
		try:
			a = rtl.set_survey(frequency=100, demod='fm')
			self.fail("expected bad frequency error")
		except rtl_app.BadFrequencyException, e:
			self.assertEquals("Bad frequency 100", e.message)

		try:
			a = rtl.set_survey(frequency=101100000, demod='nutrino')
			self.fail("expected bad frequency error")
		except rtl_app.BadDemodException, e:
			self.assertEquals("Bad demodulator 'nutrino'", e.message)

		a = rtl.stop_survey()
		self.assertEquals(None, a['demod'])
		self.assertEquals(None, a['frequency'])

		e = events.popleft()
		a = e['body']
		self.assertEquals(e['type'], 'survey')
		self.assertEquals('fm', a['demod'])
		self.assertEquals(101100000, a['frequency'])

		e = events.popleft()
		a = e['body']
		self.assertEquals(e['type'], 'survey')
		self.assertEquals(None, a['demod'])
		self.assertEquals(None, a['frequency'])

		self.assertEquals(0, len(events))

	def test_streaming(self):
		sri_packet = [None]
		data_packets = [0]

		def sri_callback(data):
			logging.debug("Got SRI %s", data)
			sri_packet[0] = data

		def data_callback(data, ts, EOS, stream_id):
			logging.debug("Got data %d bytes", len(data))
			data_packets[0] += 1

		rtl = self.rtl_app
		
		rtl.add_stream_listener(rtl.PORT_TYPE_WIDEBAND, data_callback, sri_callback)
		rtl.add_stream_listener(rtl.PORT_TYPE_NARROWBAND, data_callback, sri_callback)
		time.sleep(2)
		if sri_packet[0] or data_packets[0]:
			self.fail('Unexpected packets')

		rtl.set_survey(frequency=101100000, demod='fm')
		time.sleep(5)
		if not sri_packet[0]:
			self.fail('Missing SRI packets')

		if not data_packets[0]:
			self.fail('Missing Data packets')
		rtl.stop_survey()

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	unittest.main()
