#from ossie.utils import redhawk
#from ossie.utils.redhawk.channels import ODMListener
import collections
import threading
import time
from functools import wraps
import logging

from _common import BadDemodException, BadFrequencyException
from _utils.concurrent import background_task, safe_return_future

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

        # event listeners
        self._listeners = []

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

    def add_event_listener(self, listener):
        '''
            Adds a listener for events
        '''
        self._listeners.append(listener)

    def rm_event_listener(self, listener):
        '''
            Removes a listener for events
        '''
        # FIXME: Is this thread safe
        self._listeners.remove(listener)

    def _post_event(self, etype, body):
        ''' 
            Internal method to post a new event
        '''
        e = dict(type=etype, body=body)
        for l in self._listeners:
            try:
                l(e)
            except Exception, e:
                logging.exception('Error firing event %s to %s', e, l)


    def _set_device(self, dtype, status):
        self._device = dict(type=dtype, status=status)
        self._post_event('device', self._device)

class AsyncRTLApp(RTLApp):
    '''
        An asynchronous version of the Mock RTLApp that returns Futures and accepts callbacks.
    '''
    get_survey = background_task(RTLApp.get_survey)
    set_survey = background_task(RTLApp.set_survey)
    stop_survey = background_task(RTLApp.stop_survey)
    get_device = background_task(RTLApp.get_device)
