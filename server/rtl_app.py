#from ossie.utils import redhawk
#from ossie.utils.redhawk.channels import ODMListener
import collections
import threading
import time
import logging
import pprint
import os
from subprocess import Popen
from functools import wraps
from ossie.utils import redhawk
from ossie.utils.redhawk.channels import ODMListener
from ossie.cf import StandardEvent, ExtendedEvent, CF

from _common import BadDemodException, BadFrequencyException

def _delay(func):

    @wraps(func)
    def do_delay(self, *args, **kwargs):
        self._delayfunc(func)
        return func(self, *args, **kwargs)
    return do_delay

class RTLApp(object):
    SURVEY_DEMOD_LIST = [ "fm" ]

    FREQUENCY_RANGE = [1000000, 900000000]

    RTL_FM_WAVEFORM_ID = 'DCE:1ed946d9-3e77-4acc-8c2c-912641da6545'

    def __init__(self, domainname, delayfunc=lambda meth: None, rtlstatprog=None):
        '''
              delayfunc - a function  delay function is invoked during a call.
        '''
        self._domainname = domainname
        self._domain = None
        self._manager = None

        self._event_condition = threading.Condition()
        self._event_queue = collections.deque()
        self._survey = dict(frequency=None, demod=None)
        self._device = dict(type='rtl', status='unavailable')
        self._delayfunc = delayfunc
        if not rtlstatprog:
            bindir = "%s/../bin" % os.path.dirname(__import__(__name__).__file__)
            rtlstatprog = os.path.join(os.path.abspath(bindir), 'rtlstat.sh')
        self._rtlstat = rtlstatprog

    @_delay
    def get_survey(self):
        '''
            Return the survey properties.  A dictionary of the frequency and demodulator
            self.get_survey()
            {
                frequency: 101.0
                demod: "fm"
            }
        '''
        try:
            return dict(frequency=int(1000000 * round(self._get_manager().Frequency, 4)), demod='fm')
        except IndexError:
            return dict(frequency=None, demod=None)

    def get_available_processing(self):
        return self.SURVEY_DEMOD_LIST

    @_delay
    def set_survey(self, frequency, demod, timeout=2):
        '''
             Sets the survey properties.  Returns the new processing values.

             Raises:
                 ValueError() if a bad frequency.
                 ProcessingError() if a bad demodulator
        '''
        if demod not in self.SURVEY_DEMOD_LIST:
            raise BadDemodException(demod)

        if frequency < self.FREQUENCY_RANGE[0] or frequency > self.FREQUENCY_RANGE[1]:
            raise BadFrequencyException(frequency)

        try:
            comp = self._get_manager()
        except IndexError:
            self._launch_waveform()
            comp = self._get_manager(timeout=timeout)

        comp.Frequency = (frequency / 1000000.0)
        survey = dict(frequency=int(1000000 * round(comp.Frequency, 4)), demod='fm')
        self._post_event('survey', survey)
        return survey

    @_delay
    def stop_survey(self):
        self._stop_waveform()
        survey = dict(frequency=None, demod=None)
        self._post_event('survey', survey)
        return survey


    @_delay
    def get_device(self):
        '''
            Gets current device settings as a dictionary.

            Unavailable RTL device:
            {
                'type': 'rtl',
                'status': 'unavailable'
            }

            Ready RTL device:
            {
                'type': 'rtl',
                'status': 'ready'
            }

        '''
        # FIXME: Make in future
        try:
            p = Popen(self._rtlstat, shell=False)
            p.wait()
        except Exception, e:
            raise StandardError("%s: Failed to get device status %s" %  (self._rtlstat, str(e)))
        if p.returncode:
            return dict(type='rtl', status='unavailable')
        else:
            return dict(type='rtl', status='ready')

    @_delay
    def get_processing_list(self):
        '''
            Gets all available processing types.
        '''
        return self.SURVEY_DEMOD_LIST

    @_delay
    def next_event(self, timeout=0):
        '''
            Thread safe method for returning the next event
            available.  Returns the next event or a None if no event is available

            Possible events:
                 {
                     'type': 'survey-change'
                     'body': { ... }
                 }


                 {
                     'type': 'device-change'
                     'body': { ... }
                 }
        '''
        self._event_condition.acquire()
        try:
            if not self._event_queue and timeout > 0:
                self._event_condition.wait(timeout)

            try:
                return self._event_queue.popleft()
            except IndexError:
                return None
        finally:
            self._event_condition.release()

    def _post_event(self, etype, body):
        ''' 
            Internal method to post a new event
        '''

        self._event_condition.acquire()
        try:
            self._event_queue.append(dict(type=etype, body=body))
            self._event_condition.notify()
        finally:
            self._event_condition.release()

    def _get_domain(self):
        '''
            Returns the current connection to the domain,
            creating a connection if it's unavailable
        '''
        if not self._domain:
            self._domain =  redhawk.attach(self._domainname)
            self._odmListener = None
            # self._odmListener = ODMListener()
            # self._odmListener.connect(self._domain)
        return self._domain

    def _get_manager(self, timeout=0):
        if not self._manager:
            t = time.time()
            while not self._manager:
                try:
                    self._manager = _locate_component(self._get_domain(), 'RTL_FM_Controller_1')
                except IndexError:
                    delta = time.time() - t
                    if delta > timeout:
                        print delta
                        raise
                    time.sleep(.1)

        return self._manager
        

    def _launch_waveform(self):
        try:
            print self._get_domain().installApplication('/waveforms/Rtl_FM_Waveform/Rtl_FM_Waveform.sad.xml')
        except CF.DomainManager.ApplicationAlreadyInstalled:
            logging.info("Waveform Rtl_FM_Waveform already installed", exc_info=1)

        for appFact in self._get_domain()._get_applicationFactories():
            if appFact._get_identifier() == self.RTL_FM_WAVEFORM_ID:
                x = appFact.create('wave2', [], [])
                print "GOT X %s" % x
                x.start()
                break

    def _stop_waveform(self):
        for a in self._get_domain().apps:
            if a._get_name() == 'wave2':
                a.releaseObject()
                return
        logging.info("Waveform 'wave2' not halted - not found")




def _locate_component(domain, ident):
    logging.info("\n\nXXXXXX\nLooking for %s" % (ident,))
    idprefix = "%s:" % ident
    for app in domain.apps:
        logging.info("\n\nXXXXXX\nLooking for %s in %s" % (ident, app._get_name()))
        for comp in app.comps:
            logging.info("\n\nXXXXXX\nDoes %s match %s\n\nXXXXXX\n" % (ident, comp._id))
            if comp._id.startswith(idprefix):
                return comp
    raise IndexError('No such identifier %s' % ident)
