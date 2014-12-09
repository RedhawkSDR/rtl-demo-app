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

import pprint
import types

from ossie.utils import redhawk
from ossie.cf import StandardEvent, ExtendedEvent, CF
from ossie.properties import props_from_dict, props_to_dict

RTL_ID = 'DCE:82b9903c-6d0e-4a53-b770-bf38e35f24f6'
RTL_NAME = 'RTL2832U'

class DeviceNotFoundError(StandardError): pass

class RTL2832U(object):
    
    def __init__(self, rtldevice):
        self.device = rtldevice
    
    @staticmethod
    def locate(domain):
        if isinstance(domain, types.StringTypes):
            domainptr = redhawk.attach(domain)
        else:
            domainptr = domain
            
        for dev in domainptr.devices:
            if RTL_ID == dev._get_identifier():
                return RTL2832U(dev)
        
        raise DeviceNotFoundError(RTL_NAME)

    @staticmethod
    def get_fei_device_name():
        return RTL_NAME
    
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
        def fixd(d):
            return dict([(k.split('::')[-1], v) for k, v in d.items()])
    
        self.device.configure(props_from_dict(dict(update_available_devices=True)))
        q = props_to_dict(self.device.query(props_from_dict(dict(available_devices=None))))
        return [ fixd(d) for d in q['available_devices']]

    def set_target_hardware(self, rtlx):
        '''
            Sets the target RTL to use.  To choose a target device
            use a dictionary with the criteria to select (from the available
            rtl devices). Returns the target that was just set.

            > x.set_target_rtl(dict(index=0))
            [ {
                'index': 0,
                'name': None,
                'product': None,
                'serial': None,
                'vendor': None,
              } ]
        '''
        # the device has a bug in that if it gets the same value, it won't trigger 
        # target device.  So set it to some weird number and than change it again
        self.device.configure(dict(target_device=dict(index=-2)))

        # FIXME: Validate rtlx has the right fields
        self.device.configure(dict(target_device=rtlx))
        return props_to_dict(self.device.query(props_from_dict(dict(target_device=None))))

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-d', '--domain',
                      help='Redhawk Domain', metavar='DOMAIN',
                      default='REDHAWK_DEV')

    (options, args) = parser.parse_args()
    avail = RTL2832U.locate(options.domain).get_available_hardware()
    print "RTL Device is %s" % (avail and 'Available' or 'Unavailable')
    if avail:
        pprint.pprint(avail)
        RTL2832U.locate(options.domain).set_target_hardware(avail[0])
