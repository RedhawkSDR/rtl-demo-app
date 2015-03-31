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
import rtl_app
import time
import collections
import difflib
import logging
from rtl_app import BadFrequencyException

class RTLAppTest(unittest.TestCase):

    def setUp(self):
        # clear the running waveform before tests
        self.rtl_app = rtl_app.RTLApp("REDHAWK_TEST")
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
            self.assertEquals("Bad frequency 100", e.args[0])

        try:
            a = rtl.set_survey(frequency=101100000, demod='nutrino')
            self.fail("expected bad frequency error")
        except rtl_app.BadDemodException, e:
            self.assertEquals("Bad demodulator 'nutrino'", e.args[0])

        a = rtl.stop_survey()
        self.assertEquals(None, a['demod'])
        self.assertEquals(None, a['frequency'])

        def nextevent():
            # return only survey events
            while True:
                e = events.popleft()
                if not e:
                    break
                if e['type'] == 'survey':
                    return e

        e = nextevent()['body']
        self.assertEquals('fm', e['demod'])
        self.assertEquals(101100000, e['frequency'])

        e = nextevent()['body']
        self.assertEquals(None, e['demod'])
        self.assertEquals(None, e['frequency'])

        self.assertEquals(0, len(events))

    def test_streaming(self, porttype=rtl_app.RTLApp.PORT_TYPE_WIDEBAND):
        sri_packet = [None, None]
        data_packets = [0]

        def sri_callback(data):
            logging.debug("Got SRI %s", data)
            sri_packet[0] = data

        def sri_callback2(data):
            logging.debug("Got second SRI %s", data)
            sri_packet[1] = data

        def data_callback(data, ts, EOS, stream_id):
            logging.debug("Got data %d bytes", len(data))
            data_packets[0] += 1

        rtl = self.rtl_app
        
        rtl.add_stream_listener(porttype, data_callback, sri_callback)
        time.sleep(2)
        if sri_packet[0] or data_packets[0]:
            self.fail('Unexpected packets')

        rtl.set_survey(frequency=101100000, demod='fm')
        time.sleep(5)
        if not sri_packet[0]:
            self.fail('Missing SRI packets')

        if not data_packets[0]:
            self.fail('Missing Data packets')
            
        # now add listener later and verify a second SRI
        rtl.add_stream_listener(porttype, data_callback, sri_callback2)
        if not sri_packet[1]:
            self.fail('Missing second SRI packets')
        rtl.stop_survey()

    def test_streaming_narrow(self):
        self.test_streaming(porttype=rtl_app.RTLApp.PORT_TYPE_NARROWBAND)

    def test_rds(self):
        rtl = self.rtl_app

        events = collections.deque()
        def elisten(event):
            events.append(event)
        rtl.add_event_listener(elisten)

        a = rtl.set_survey(frequency=101100000, demod='fm')
        time.sleep(2)
        a = rtl.stop_survey()

        # test all of the events and get the max similarity
        def maxsimilar(smap, event, field, value, threshold=.5):
            # print event
            s = self.similarity(value, event[field])
            v = dict(similarity=s, best=event[field], value=value, threshold=threshold)
            if s >= smap.get(field, v)['similarity']:
                smap[field] = v

        m = {}
        for e in events:
            if e['type'] != 'rds':
                continue
            maxsimilar(m, e['body'], 'Full_Text', 'REDHAWK Radio, Rock the Hawk! (www.redhawksdr.org)', .05)
            maxsimilar(m, e['body'], 'Short_Text', '100.1 FM', .3)
            maxsimilar(m, e['body'], 'Call_Sign', 'WSDR')
            maxsimilar(m, e['body'], 'Group', '0A')
            maxsimilar(m, e['body'], 'TextFlag', 'A')
            maxsimilar(m, e['body'], 'PI_String', '848F')
        
        issues = filter(lambda x: x[1]['similarity'] < x[1]['threshold'], m.items())
        if issues:
            self.fail("Bad fields %s" % issues)


    def test_bad_frequency_when_off(self):
        rtl = self.rtl_app
        
        # verify tuner is off
        self.assertEquals(None, rtl.get_survey()['frequency'])
        
        try:
            # set tuner to bad frequency. Should get error
            a = rtl.set_survey(frequency=25000000, demod='fm')
            self.fail("Expected exception, got %s" % a)
        except BadFrequencyException, e:
            pass
        # validate tuner still should be off
        self.assertEquals(None, rtl.get_survey()['frequency'])
        
        a = rtl.stop_survey()

    def test_bad_frequency_when_on(self):
        rtl = self.rtl_app
        good_freq = 102000000        

        # set tuner to bad frequency. Should get error
        a = rtl.set_survey(frequency=good_freq, demod='fm')
        self.assertEquals(good_freq, rtl.get_survey()['frequency'])

        try:
            # set tuner to bad frequency. Should get error
            a = rtl.set_survey(frequency=25000000, demod='fm')
            self.fail("Expected exception, got %s" % a)
        except BadFrequencyException, e:
            pass
        
        # validate tuner still should be off
        self.assertEquals(good_freq, rtl.get_survey()['frequency'])

        a = rtl.stop_survey()


    def similarity(self, str1, str2):
        return difflib.SequenceMatcher(lambda x: x == ' ', str1, str2).ratio()


if __name__ == '__main__':
    print "Run REDHAWK_TEST"
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
