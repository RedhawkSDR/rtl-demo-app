#!/usr/bin/env python

import pprint
import types

from ossie.utils import redhawk
from ossie.cf import StandardEvent, ExtendedEvent, CF
from ossie.properties import props_from_dict, props_to_dict

SIM_ID = 'DCE:6e71da01-9e7f-4b8a-838c-8f1d59d6dd9c'

class DeviceNotFoundError(StandardError): pass

class sim_RX_DIGITIZER(object):
    
    def __init__(self, rtldevice):
        self.device = rtldevice
    
    @staticmethod
    def locate(domain):
        if isinstance(domain, types.StringTypes):
            domainptr = redhawk.attach(domain)
        else:
            domainptr = domain
            
        for dev in domainptr.devices:
            SIM_ID == dev._get_identifier()
            return sim_RX_DIGITIZER(dev)
        
        raise DeviceNotFoundError('sim_RX_DIGITIZER')
    
    def get_available_hardware(self):
        '''
            Returns a list of the available RTL devices
            >> x.get_vailable_rtl()
             [ {
                'index': 0,
                'name': 'ezcap USB 2.0 DVB-T/DAB/FM dongle',
                'product': 'RTL2838UHIDIR',
                'serial': '000000000',
                'vendor': 'Realtek'
               } ]
        '''
        return [{
                'index': 0,
                'name': 'sim_RX_DIGITIZER',
                'product': 'sim_RX_DIGITIZER',
                'serial': '000000000',
                'vendor': 'USG'
               }]


    def set_target_hardware(self, rtlx):
        '''
            Sets the target hardware to use.  This is a noop function.
        '''
        pass

if __name__ == '__main__':
    avail = sim_RX_DIGITIZER.locate('REDHAWK_DEV').get_available_hardware()
    print "RTL Device is %s" % (avail and 'Available' or 'Unavailable')
    if avail:
        pprint.pprint(avail)
        sim_RX_DIGITIZER.locate('REDHAWK_DEV').set_target_hardware(avail[0])
