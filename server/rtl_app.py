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
from ossie.cf import StandardEvent, ExtendedEvent, CF

from rest.asyncport import AsyncPort

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
    RTL_FM_WAVEFORM_ID = 'DCE:1ed946d9-3e77-4acc-8c2c-912641da6545'
    PORT_TYPE_WIDEBAND = 'wideband%s'
    PORT_TYPE_NARROWBAND = 'narrowband%s'

    def __init__(self, domainname, delayfunc=lambda meth: None, rtlstatprog=None):
        '''
              delayfunc - a function  delay function is invoked during a call.
        '''
        self._domainname = domainname
        self._domain = None
        self._components = {}
        self._process = None

        # event listeners
        self._listeners = {
           'event': [],
           RTLApp.PORT_TYPE_WIDEBAND%'data': [],
           RTLApp.PORT_TYPE_WIDEBAND%'sri': [],
           RTLApp.PORT_TYPE_NARROWBAND%'data': [],
           RTLApp.PORT_TYPE_NARROWBAND%'sri': []
        }
        
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
        except (IndexError, StandardError):
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
        self._stop_application()    
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

    def add_event_listener(self, listener):
        '''
            Adds a listener for events
        '''
        self._listeners['event'].append(listener)

    def rm_event_listener(self, listener):
        '''
            Removes a listener for events
        '''
        # FIXME: Is this thread safe
        self._listeners['event'].remove(listener)

    def add_stream_listener(self, portname, data_listener, sri_listener=None):
        '''
             Adds a listener for streaming (SRI and Data).

             e.g.
             >>> add_stream_listener(PORTTYPE_WIDEBAND, my_data_listener, my_sri_listener)
        '''
        self._init_psd_listeners()
        self._listeners[portname%'data'].append(data_listener)
        if sri_listener:
            self._listeners[portname%'sri'].append(sri_listener)

    def rm_stream_listener(self, portname, data_listener, sri_listener=None):
        '''
             Adds a listener for streaming (SRI and Data).

             e.g.
             >>> add_stream_listener(PORTTYPE_WIDEBAND, my_data_listener, my_sri_listener)
        '''
        try:
            self._listeners[portname%'data'].remove(data_listener)
        except ValueError:
            pass
        if sri_listener:
            try:
                self._listeners[portname%'sri'].remove(sri_listener)
            except ValueError:
                pass


    def _post_event(self, etype, body):
        ''' 
            Internal method to post a new event
        '''
        e = dict(type=etype, body=body)
        for l in self._listeners['event']:
            try:
                l(e)
            except Exception:
                logging.exception('Error firing event %s to %s', e, l)


    def _get_domain(self):
        '''
            Returns the current connection to the domain,
            creating a connection if it's unavailable
        '''
        self._start_application(self._domainname)
        if not self._domain:
            self._domain =  redhawk.attach(self._domainname)
            self._domain._odmListener = None
            # self._odmListener = ODMListener()
            # self._odmListener.connect(self._domain)
        return self._domain

    def _get_component(self, compname, timeout=1):
        if not self._components.get(compname, None):
            t = time.time()
            while not self._components.get(compname, None):
                try:
                    self._components[compname] = _locate_component(self._get_domain(), compname)
                except IndexError:
                    delta = time.time() - t
                    if delta > timeout:
                        raise
                    time.sleep(.1)

        return self._components[compname]


    def _get_manager(self, timeout=0):
        return self._get_component('RTL_FM_Controller_1')
        

    def  _init_psd_listeners(self):
        self._push_sri_psd1 = self._generate_bulkio_callback(self.PORT_TYPE_WIDEBAND, 'sri')
        self._push_packet_psd1 = self._generate_bulkio_callback(self.PORT_TYPE_WIDEBAND, 'data')
        self._push_sri_psd2 = self._generate_bulkio_callback(self.PORT_TYPE_NARROWBAND, 'sri')
        self._push_packet_psd2 = self._generate_bulkio_callback(self.PORT_TYPE_NARROWBAND, 'data')

        port = self._get_component('psd_1').getPort('fft_dataFloat_out')
        self._psd1_port = AsyncPort(AsyncPort.PORT_TYPE_FLOAT, self._push_sri_psd1, self._push_packet_psd1)
        port.connectPort(self._psd1_port.getPort(), "psd1_%s" % id(self))
        port = self._get_component('psd_2').getPort('fft_dataFloat_out')
        self._psd2_port = AsyncPort(AsyncPort.PORT_TYPE_FLOAT, self._push_sri_psd2, self._push_packet_psd2)
        port.connectPort(self._psd2_port.getPort(), "psd2_%s" % id(self))

    def _generate_bulkio_callback(self, portname, data_type):
        '''
            Generates a callback function that 
            a listener for a [port + data_type] combination.

            Valid portnames: PORT_TYPE_*
            Valid data types: 'sri' or 'data' (the bulkio packet)
        '''

        def bulkio_callback_func(*args):
            for l in self._listeners[portname % data_type]:
                try:
                    l(*args)
                except Exception, e:
                    logging.exception('Error firing event %s to %s', args, l)
        return bulkio_callback_func


    def _launch_waveform(self):
        try:
            self._get_domain().installApplication('/waveforms/Rtl_FM_Waveform/Rtl_FM_Waveform.sad.xml')
        except CF.DomainManager.ApplicationAlreadyInstalled:
            logging.info("Waveform Rtl_FM_Waveform already installed", exc_info=1)

        for appFact in self._get_domain()._get_applicationFactories():
            if appFact._get_identifier() == self.RTL_FM_WAVEFORM_ID:
                x = appFact.create('wave2', [], [])
                x.start()
                break

    def _stop_waveform(self):
        for a in self._get_domain().apps:
            if a._get_name() == 'wave2':
                a.releaseObject()
                return
        logging.info("Waveform 'wave2' not halted - not found")


    def _start_application(self, domain):
        if not self._process or self._process.poll() is not None:
            logging.debug("Start domain %s", domain)
            self._process = Popen(('../bin/startdomain.sh', '-d', domain), shell=False)
            # FIXME: Determine if domain is running other than sleeping
            time.sleep(1)

    def _stop_application(self):
        if self._process:
            try:
                logging.debug("stopping domain")
                self._process.kill()
                self._process.wait(2)
            except OSError:
                logging.warn("Unable to kill process %d" % self._process.pid, exc_info=1)
        self._domain = None
        self._components = {}
        self._process = None


def _locate_component(domain, ident):
    logging.debug("Looking for component %s", ident)
    idprefix = "%s:" % ident
    for app in domain.apps:
        for comp in app.comps:
            if comp._id.startswith(idprefix):
                return comp
    logging.debug("Was not able to find component %s", ident)
    raise IndexError('No such identifier %s' % ident)


class AsyncRTLApp(RTLApp):
    '''
        An asynchronous version of the RTLApp that returns Futures and accepts callbacks.
    '''
    get_survey = background_task(RTLApp.get_survey)
    set_survey = background_task(RTLApp.set_survey)
    stop_survey = background_task(RTLApp.stop_survey)
    get_device = background_task(RTLApp.get_device)
