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

SIM_ID = 'FmRdsSimulatorNode:FmRdsSimulator_1'
SIM_NAME = 'FmRdsSimulator'

class DeviceNotFoundError(StandardError): pass

class sim_FM_Device(object):

  def __init__(self, rtldevice):
    self.device = rtldevice

  @staticmethod
  def locate(domain):
    if isinstance(domain, types.StringTypes):
      domainptr = redhawk.attach(domain)
    else:
      domainptr = domain

    for dev in domainptr.devices:
      if SIM_ID == dev._get_identifier():
        return sim_FM_Device(dev)

    raise DeviceNotFoundError(SIM_NAME)

  @staticmethod
  def get_fei_device_name():
    return SIM_NAME

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
              'name': 'sim_FM_DIGITIZER',
              'product': 'sim_FM_DIGITIZER',
              'serial': '000000000',
              'vendor': 'USG'
            }]


  def set_target_hardware(self, rtlx):
    '''
        Sets the target hardware to use.  This is a noop function.
    '''
    pass

if __name__ == '__main__':
  avail = sim_FM_Device.locate('REDHAWK_DEV').get_available_hardware()
  print "SIM Device is %s" % (avail and 'Available' or 'Unavailable')
  if avail:
    pprint.pprint(avail)
    sim_FM_Device.locate('REDHAWK_DEV').set_target_hardware(avail[0])
