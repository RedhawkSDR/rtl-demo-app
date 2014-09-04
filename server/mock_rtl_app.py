#from ossie.utils import redhawk
#from ossie.utils.redhawk.channels import ODMListener
import collections
import threading
import time
from functools import wraps

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

    def __init__(self, domainname, delayfunc=lambda meth: None):
        '''
              The delay function is invoked during a call.
        '''
        self._domainname = domainname

        self._event_condition = threading.Condition()
        self._event_queue = collections.deque()
        self._survey = dict(frequency=None, demod=None)
        self._device = dict(type='rtl', status='unavailable')
        self._delayfunc = delayfunc


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
        # FIXME: Connect with FrontEnd device and processing mode
        return self._survey

    def get_available_processing(self):
        return self.SURVEY_DEMOD_LIST

    @_delay
    def set_survey(self, frequency, demod, timeout=5):
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

        self._survey = dict(frequency=int(frequency), demod=demod)
        self._post_event('survey', self._survey)
        return self._survey

    @_delay
    def stop_survey(self):
        self._survey = dict(frequency=None, demod=None)
        self._post_event('survey', self._survey)
        return self._survey


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
        return self._device

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

    def _set_device(self, dtype, status):
        self._device = dict(type=dtype, status=status)
        self._post_event('device', self._device)