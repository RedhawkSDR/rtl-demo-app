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
import threading
import time
import logging
import pprint

import uuid

from ossie.utils import redhawk
from ossie.events import GenericEventConsumer
from ossie import properties

from asyncport import AsyncPort
from _common import BadDemodException, BadFrequencyException, DeviceUnavailableException
from _utils.tasking import background_task
from devices import RTL2832U, sim_FM_Device

SRI_MODE_TO_ATOMS = {
    0: 1,    # scalar - 1 element per atom
    1: 2     # complex - 2 elements per atom
}


def _split_frame(data, frame_size):
    '''
        Splits a data into discrete frames.  Data must be evenly divisible by packet size
        Returns a tuple of packet + flag, the flag being True when it's the last packet

        >>> d = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        >>> [ x for x in _split_frame(d, 3)]
        [([1, 2, 3], False), ([4, 5, 6], False), ([7, 8, 9], False), ([10, 11, 12], True)]
        >>> [x for x in _split_frame(d, 4)]
        [([1, 2, 3, 4], False), ([5, 6, 7, 8], False), ([9, 10, 11, 12], True)]
        >>> [x for x in _split_frame(d, 6)]
        [([1, 2, 3, 4, 5, 6], False), ([7, 8, 9, 10, 11, 12], True)]
        >>> [x for x in _split_frame(d, 1)]
        [([1], False), ([2], False), ([3], False), ([4], False), ([5], False), ([6], False), ([7], False), ([8], False), ([9], False), ([10], False), ([11], False), ([12], True)]
        >>> [x for x in _split_frame(d, 2)]
        [([1, 2], False), ([3, 4], False), ([5, 6], False), ([7, 8], False), ([9, 10], False), ([11, 12], True)]
        >>> [x for x in _split_frame(d, 12)]
        [([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], True)]
    '''

    p = len(data) / frame_size
    for f in xrange(p-1):
        yield (data[f * frame_size:(f+1)*frame_size], False)
    yield (data[(p-1)* frame_size:p*frame_size], True)


class StreamingBridge(object):
    '''
        Tracks streaming data and splits it up into single frames
    '''
    def __init__(self, name):
        self.name = name
        self._identity = "BulkIO bridge %s" % name
        self.last_sri = None
        self._packets = []
        self._data_listeners = []
        self._sri_listeners = []
        self._lock = threading.RLock()
        self._log = logging.getLogger("bulkio_bridge")
        self._connection_name = None
        self._their_port = None
        self._our_port = None

    def add_data_listener(self, data_listener):
        with self._lock:
            self._data_listeners.append(data_listener)

    def add_sri_listener(self, sri_listener):
        with self._lock:
            self._sri_listeners.append(sri_listener)
            if self.last_sri:
                try:
                    sri_listener(self.last_sri)
                except Exception, e:
                    self._log.exception('%s: Error firing sri %s', self._identity, e.args)

    def rm_data_listener(self, data_listener):
        with self._lock:
            try:
                self._data_listeners.remove(data_listener)
            except ValueError:
                self._log.warn("%s: Data listener %s not found", self._identity, data_listener)

    def rm_sri_listener(self, sri_listener):
        with self._lock:
            try:
                self._sri_listeners.remove(sri_listener)
            except ValueError:
                self._log.warn("%s: SRI listener %s not found", self._identity, sri_listener)

    def _push_sri(self, SRI):
        with self._lock:
            self._log.debug("%s: got SRI packet %s", self._identity, SRI)
            try:
                self._frame_size = SRI.subsize * SRI_MODE_TO_ATOMS[SRI.mode]
                self.last_sri = SRI
            except IndexError:
                self._log.error("%s: Unknown SRI mode %s", self._identity, SRI.mode)

            for l in self._sri_listeners:
                try:
                    l(SRI)
                except Exception, e:
                    self._log.exception('%s: Error firing sri %s to %s', self._identity, args, l)
        
    def _push_data(self, data, ts, EOS, stream_id):
        with self._lock:
            if not self.last_sri:
               self._log.debug("%s: Got %b packet before SRI.  Tossing", self._identity, len(data))
               return

            if self._frame_size:
                frame_size = self._frame_size if self._frame_size else len(data)
                remainder = len(data) % frame_size

                if remainder:
                    self._log.warn("%s: Unexpected packet size.  Not divisible by frame size.  Packet=%d, frame=%d, modulus=%d",
                                   self._identity, len(data), frame_size, remainder)

                # FIXME: timestamp is not coherent for subpackets
                for f in _split_frame(data, frame_size):
                    self._push_frame(f[0], ts, f[1] and EOS, stream_id)
            else:
                self._push_frame(data, ts, EOS, stream_id)

    def _push_frame(self, data, ts, EOS, stream_id):
        with self._lock:
            for l in self._data_listeners:
                try:
                    l(data, ts, EOS, stream_id)
                except Exception, e:
                    self._log.exception('%s: Error firing data %s to %s', self._identity, e.args, l)

    def connectPort(self, port, datatype):
        with self._lock:
            self._their_port = port
            self._our_port = AsyncPort(datatype, self._push_sri, self._push_data)
            connection =  "%s_bridge_%s" % (self.name, id(self))
            self._their_port.connectPort(self._our_port.getPort(), connection)
            self._connection_name = connection

    def disconnectPort(self):
        with self._lock:
            if self._connection_name:
                try:
                    self._their_port.disconnectPort(self._connection_name)
                except Exception:
                    self._log.exception("%s: Unable to detach port %s", self._identity, self._connection_name)
            self._their_port = None
            self._our_port = None
            self._connection_name = None
    

class RTLApp(object):

    SURVEY_DEMOD_LIST = [ "fm" ]
    FREQUENCY_RANGE = [1000000, 900000000]
    RTL_FM_WAVEFORM_ID = 'DCE:1ed946d9-3e77-4acc-8c2c-912641da6545'

    PORT_TYPE_WIDEBAND = 'wideband'
    PORT_TYPE_NARROWBAND = 'narrowband'
    PORT_TYPE_FM = 'fm'
    PORT_TYPE_AUDIO_RAW = 'audio_raw'
    PORT_TYPE_PSK_SHORT = 'psk_short'
    PORT_TYPE_PSK_FLOAT = 'psk_float'

    def __init__(self, domainname, frontend=sim_FM_Device):
        '''
              Instantiate the RTL Application against the given redhawk domain.
        '''
        self._log = logging.getLogger('RTLApp')
        self._domainname = domainname
        self._frontend = frontend

        self._waveform_name = "rtl_waveform_%s" % id(self)
        self._device_available = False
        self._event_consumer_id = None
        self._event_consumer = None

        # initialize event listener dict
        self._event_listeners = []
        self._bulkio_bridges = {
           self.PORT_TYPE_WIDEBAND: StreamingBridge('wideband'),
           self.PORT_TYPE_NARROWBAND: StreamingBridge('narrowband'),
           self.PORT_TYPE_FM: StreamingBridge('FM'),
           self.PORT_TYPE_AUDIO_RAW: StreamingBridge('audio_raw'),
           self.PORT_TYPE_PSK_FLOAT: StreamingBridge('psk_float'),
           self.PORT_TYPE_PSK_SHORT: StreamingBridge('psk_short'),
        }

        self._clear_redhawk()

        # intialize default values
        self._survey = dict(frequency=None, demod=None)
        self._device = dict(type=self._frontend.get_fei_device_name(), status='unavailable')


    def _clear_redhawk(self):
        # clear the REDHAWK cache
        #self._close_psd_listeners()
        if self._event_consumer_id and self._domain:
            try:
                self._domain.unregisterFromEventChannel(self._event_consumer_id, 'RBDS_Channel')
            except Exception, e:
                self._log.exception("domain.unregisterFromEventChannel(%s, 'RBDS_Channel') failed" % self._event_consumer_id)
        self._event_consumer_id = None
        # TODO:  Does this actually delete CORBA Servant?
        self._event_consumer = None
        self._domain = None
        self._components = {}
        self._process = None
        self._waveform = None

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
            # Have to cast to an int because type is not a python int!
            return dict(frequency=int(1000000 * round(self._get_manager().TuneRequest.frequency, 4)), 
                        demod_if=int(self._get_tfd().TuningIF),
                        demod='fm')
        except (IndexError, StandardError):
            return dict(frequency=None, demod_if=None, demod=None)

    def get_available_processing(self):
        return self.SURVEY_DEMOD_LIST

    def set_survey(self, frequency, demod_if, demod, timeout=2):
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

        # property to restore
        kill_waveform = not self._waveform
            
        self._launch_waveform()
        # First try to set the device RF frequency.  If that fails
        # the ensure survey fails
        comp = self._get_manager(timeout=timeout)
        comp.TuneRequest.frequency = (frequency / 1000000.0)
        actual = 1000000 * round(comp.TuneRequest.frequency, 4)
        
        if abs(actual - frequency) > 10000:
            # bad frequency.  Restore
            if kill_waveform:
                self._stop_waveform()
                self._clear_redhawk()
            raise BadFrequencyException(frequency)

        # Now try to set the TuneFilterDecimate TuningIF.  That should work
        tfd = self._get_tfd(timeout=timeout)
        tfd.TuningIF = demod_if

        # Have to cast to an int because type is not a python int!
        survey = dict(frequency=actual, demod_if=int(tfd.TuningIF), demod='fm')

        self._post_event('survey', survey)
        return survey

    def stop_survey(self):
        #self._close_psd_listeners()
        self._stop_waveform()
        self._clear_redhawk()

        survey = dict(frequency=None, demod_if=None, demod=None)
        self._post_event('survey', survey)
        return survey


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
        self.poll_device_status()
        return self._device

    def set_simulation(self, use_simulator):
        '''
            Switch from using a real device to using a simulation.

        :param use_simulator: Whether to use a simulator
        '''

        if use_simulator and self._frontend.is_simulator():
            return Exception("Already using a simulator")

        if not use_simulator and not self._frontend.is_simulator():
            return Exception("Already using a hardware device")

        if self._waveform:
            return Exception("Cannot perform on running Waveform")

        logging.warn("SUCCESS")

        if use_simulator:
            self._frontend = sim_FM_Device
        else:
            self._frontend = RTL2832U
        return self.poll_device_status()

    def poll_device_status(self):
        '''
            fetch the RTL device and check hardware availability.
        '''
        rtl = self._frontend.locate(self._get_domain())
        avail = rtl.get_available_hardware()
        status = 'ready' if avail else 'unavailable'

        self._device = dict(
            type=self._frontend.get_fei_device_name(),
            simulator=self._frontend.is_simulator(),
            status=status)

        # if the availability has changed ...
        if self._device_available != bool(avail):
            if avail:
                # set the target RTL device (so it is available to be allocated)
                rtl.set_target_hardware(avail[0])
            else:
                # FIXME: device is now gone - what action to take
                self._stop_waveform()

            self._device_available = bool(avail) 
            self._post_event('device', self._device)

        return self._device_available

    def get_processing_list(self):
        '''
            Gets all available processing types.
        '''
        return self.SURVEY_DEMOD_LIST

    def add_event_listener(self, listener):
        '''
            Adds a listener for events
        '''
        self._event_listeners.append(listener)

    def rm_event_listener(self, listener):
        '''
            Removes a listener for events
        '''
        # FIXME: Is this thread safe
        self._event_listeners.remove(listener)

    def add_stream_listener(self, portname, data_listener, sri_listener=None):
        '''
             Adds a listener for streaming (SRI and Data).

             e.g.
             > add_stream_listener(PORT_TYPE_WIDEBAND, my_data_listener, my_sri_listener)
        '''
        self._bulkio_bridges[portname].add_data_listener(data_listener)
        if sri_listener:
            self._bulkio_bridges[portname].add_sri_listener(sri_listener)
           
    def rm_stream_listener(self, portname, data_listener, sri_listener=None):
        '''
             Adds a listener for streaming (SRI and Data).

             e.g.
             > add_stream_listener(PORT_TYPE_WIDEBAND, my_data_listener, my_sri_listener)
        '''
        self._bulkio_bridges[portname].rm_data_listener(data_listener)
        if sri_listener:
            self._bulkio_bridges[portname].rm_sri_listener(sri_listener)

    def _post_event(self, etype, body):
        ''' 
            Internal method to post a new event
        '''
        e = dict(type=etype, body=body)
        for l in self._event_listeners:
            try:
                l(e)
            except Exception:
                self._log.exception('Error firing event %s to %s', e, l)


    def _get_domain(self):
        '''
            Returns the current connection to the domain,
            creating a connection if it's unavailable
        '''
        if not self._domain:
            self._init_application()
        return self._domain

    def _get_component(self, compname, timeout=1):
        if not self._components.get(compname, None):
            t = time.time()
            while not self._components.get(compname, None):
                try:
                    self._components[compname] = self._locate_component(self._get_domain(), compname)
                except IndexError:
                    delta = time.time() - t
                    if delta > timeout:
                        raise
                    time.sleep(.1)

        return self._components[compname]


    def _get_manager(self, timeout=0):
        return self._get_component('FrontEndController_1')

    def _get_tfd(self, timeout=0):
        return self._get_component('TuneFilterDecimate_1')

    def  _init_psd_listeners(self):
        port = self._get_component('wideband_psd').getPort('psd_dataFloat_out')
        self._bulkio_bridges[RTLApp.PORT_TYPE_WIDEBAND].connectPort(port, AsyncPort.PORT_TYPE_FLOAT)

        port = self._get_component('narrowband_psd').getPort('psd_dataFloat_out')
        self._bulkio_bridges[RTLApp.PORT_TYPE_NARROWBAND].connectPort(port, AsyncPort.PORT_TYPE_FLOAT)

        port = self._get_component('fm_psd').getPort('psd_dataFloat_out')
        self._bulkio_bridges[RTLApp.PORT_TYPE_FM].connectPort(port, AsyncPort.PORT_TYPE_FLOAT)

        port = self._get_component('ArbitraryRateResampler_1').getPort('dataFloat_out')
        self._bulkio_bridges[RTLApp.PORT_TYPE_AUDIO_RAW].connectPort(port, AsyncPort.PORT_TYPE_FLOAT)

        port = self._get_component('psk_soft_1').getPort('dataFloat_out')
        self._bulkio_bridges[RTLApp.PORT_TYPE_PSK_FLOAT].connectPort(port, AsyncPort.PORT_TYPE_FLOAT)

        port = self._get_component('psk_soft_1').getPort('dataShort_out')
        self._bulkio_bridges[RTLApp.PORT_TYPE_PSK_SHORT].connectPort(port, AsyncPort.PORT_TYPE_SHORT)

    def _close_psd_listeners(self):
        for s in self._bulkio_bridges.values():
            s.disconnectPort()

    def _init_application(self):
        
         #  [{'id': 'RBDS_Output', 'value': 
         #      [{'id': 'RBDS_Output::Full_Text', 'value': 'REDHAWK Radio, Rock the Hawk! (www.redhawksdr.org)              '},
         #       {'id': 'RBDS_Output::Short_Text', 'value': 'REDHAWK!'}, {'id': 'RBDS_Output::Station_Type', 'value': 'None'}, 
         #       {'id': 'RBDS_Output::Call_Sign', 'value': 'WSDR'}, 
         #       {'id': 'RBDS_Output::PI_String', 'value': '848F'}, 
         #       {'id': 'RBDS_Output::Group', 'value': '0A'}, 
         #       {'id': 'RBDS_Output::TextFlag', 'value': 'A'}]}]
        
        def post_event(event, typecode):            
            # pprint.pprint(event)
            d = properties.props_to_dict(event)
            self._post_event('rds', _rds_map_translate(d['RBDS_Output']))
            
        self._domain = redhawk.attach(self._domainname)
        self._event_consumer = GenericEventConsumer(post_event, keep_structs=True)
        self._event_consumer_id = str(uuid.uuid1())
        self._domain.registerWithEventChannel(self._event_consumer._this(), self._event_consumer_id, 'RBDS_Channel')
        #self._odmListener = ODMListener()
        #self._odmListener.connect(self._domain)

    def _launch_waveform(self):
        if self._waveform:
            return

        # update device status (can't use self.poll_device_status() because it may be async)
        RTLApp.poll_device_status(self)

        if not self._device_available:
            raise DeviceUnavailableException('No RTL device available on the system')

        try:        
            self._log.info("About to create Rtl_FM_Waveform")
            self._waveform = self._get_domain().createApplication('RTL_FM_Waveform')
            self._waveform_name = self._waveform.name

            comp = self._get_manager()
            comp.FEIDevice.deviceName = self._frontend.get_fei_device_name()

            #FIXME: sleeps are evil
            time.sleep(1)
            self._log.debug("Waveform %s created", self._waveform_name)
            self._waveform.start()
            self._log.debug("Waveform %s started", self._waveform_name)
            time.sleep(2)
            self._init_psd_listeners()
            self._log.debug("PSD listeners initialized %s", self._waveform_name)
        except Exception:
            self._log.exception("Unable to start waveform")
            raise

    def _stop_waveform(self):
        if self._waveform:
            self._waveform.releaseObject()
            self._waveform = None


    def _locate_component(self, domain, ident):
        self._log.debug("Looking for component %s", ident)
        idprefix = "%s:" % ident
        for app in domain.apps:
            for comp in app.comps:
                if comp._id.startswith(idprefix):
                    return comp
        self._log.debug("Was not able to find component %s", ident)
        raise IndexError('No such identifier %s' % ident)

def _rds_map_translate(rds_event_map):
    return dict([(k.replace('RBDS_Output::', ''), v) for k, v in rds_event_map.items()])

class AsyncRTLApp(RTLApp):
    '''
        An asynchronous version of the RTLApp that returns Futures and accepts callbacks.
    '''
    get_survey = background_task(RTLApp.get_survey)
    set_survey = background_task(RTLApp.set_survey)
    stop_survey = background_task(RTLApp.stop_survey)
    get_device = background_task(RTLApp.get_device)
    set_simulation = background_task(RTLApp.set_simulation)
    poll_device_status = background_task(RTLApp.poll_device_status)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
