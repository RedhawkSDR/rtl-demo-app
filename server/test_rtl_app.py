#!/usr/bin/env python
import unittest
import sys
import rtl_app
import time

class RTLAppTest(unittest.TestCase):

	def setUp(self):
		# clear the running waveform before tests
		rtl_app.RTLApp("REDHAWK_DEV").stop_survey()

	def test_halt(self, rtl=None):
		if not rtl:
			#rtl = rtl_app.MockRTLApp("domain")
			rtl = rtl_app.RTLApp("REDHAWK_DEV")
		a = rtl.set_survey(frequency=101100000, demod='fm')
		a = rtl.stop_survey()
		self.assertEquals(None, a['frequency'])
		self.assertEquals(None, a['demod'])


	def test_survey(self, rtl=None):
		if not rtl:
			#rtl = rtl_app.MockRTLApp("domain")
			rtl = rtl_app.RTLApp("REDHAWK_DEV")
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

		e = rtl.next_event(timeout=1)
		a = e['body']
		self.assertEquals(e['type'], 'survey')
		self.assertEquals('fm', a['demod'])
		self.assertEquals(101100000, a['frequency'])
		e = rtl.next_event(timeout=1)
		a = e['body']
		self.assertEquals(e['type'], 'survey')
		self.assertEquals(None, a['demod'])
		self.assertEquals(None, a['frequency'])
		e = rtl.next_event(timeout=.5)
		self.assertEquals(None, e)
		e = rtl.next_event()
		self.assertEquals(None, e)

	def test_survey_delay(self):
		#self.test_survey(rtl_app.MockRTLApp("domain", lambda f: sys.stdout.write("Func %s\n" % f)))
		self.test_survey(rtl_app.RTLApp("REDHAWK_DEV", lambda f: sys.stdout.write("Func %s\n" % f)))


if __name__ == '__main__':
	unittest.main()
