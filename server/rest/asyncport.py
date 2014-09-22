#
# This file is protected by Copyright. Please refer to the COPYRIGHT file 
# distributed with this source distribution.
# 
# This file is part of REDHAWK core.
# 
# REDHAWK core is free software: you can redistribute it and/or modify it under 
# the terms of the GNU Lesser General Public License as published by the Free 
# Software Foundation, either version 3 of the License, or (at your option) any 
# later version.
# 
# REDHAWK core is distributed in the hope that it will be useful, but WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS 
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
# 
# You should have received a copy of the GNU Lesser General Public License 
# along with this program.  If not, see http://www.gnu.org/licenses/.
#

import logging
from new import classobj
from bulkio.bulkioInterfaces import BULKIO, BULKIO__POA

        
class AsyncPort(object):
    
    PORT_TYPE_FLOAT = BULKIO__POA.dataFloat
    PORT_TYPE_DOUBLE = BULKIO__POA.dataDouble
    PORT_TYPE_SHORT = BULKIO__POA.dataShort
    PORT_TYPE_CHAR = BULKIO__POA.dataChar
    PORT_TYPE_LONG = BULKIO__POA.dataLong
    PORT_TYPE_LONG_LONG = BULKIO__POA.dataLongLong
    PORT_TYPE_OCTET = BULKIO__POA.dataOctet


    """
        A port that uses callbacks for SRI and data.
    """
    def __init__(self, porttype, pushSRI, pushPacket):
        """        
        Inputs:
            :porttype        The BULKIO__POA data type
        """
        self.port_type = porttype
        self.last_sri = BULKIO.StreamSRI(1, 0.0, 0.001, 1, 200, 0.0, 0.001, 1,
                                    1, "defaultStreamID", True, [])
        self.last_packet = []
        self.eos = False

        self._pushSRI_callback = pushSRI
        self._pushPacket_callback = pushPacket

        self._logger = logging.getLogger(self.__class__.__name__)
    
    def start(self):
        self.eos = False
        
    def _pushSRI(self, H):
        """
        Stores the SteramSRI object regardless that there is no need for it

        Input:
            <H>    The StreamSRI object containing the information required to
                   generate the header file
        """
        self.last_sri = H
        try:
            self._pushSRI_callback(H)
        except Exception, e:
            self._logger.exception("PUSH SRI Failure")
        
    def _pushPacket(self, data, ts, EOS, stream_id):
        """
        Appends the data to the end of the array.
        
        Input:
            <data>        The actual data to append to the array
            <ts>          The timestamp
            <EOS>         Flag indicating if this is the End Of the Stream
            <stream_id>   The unique stream id
        """
        if EOS:
            self.eos = True

        self.last_packet = data
        try:
            self._pushPacket_callback(data, ts, EOS, stream_id)
        except Exception, e:
            self._logger.exception("PushPacket Failure ts=%s, EOS=%s, stream_id=%s, data=%d elements", ts, EOS, stream_id, len(data))
            
    def getPort(self):
        """
        Returns a Port object of the same type as the one specified as the 
        porttype argument during the object instantiation.  It uses the 
        classobj from the new module to generate a class on runtime.

        The classobj generates a class using the following arguments:
        
            name:        The name of the class to generate
            bases:       A tuple containing all the base classes to use
            dct:         A dictionary containing all the attributes such as
                         functions, and class variables
        
        It is important to notice that the porttype is a BULKIO__POA type and
        not a BULKIO type.  The reason is because it is used to generate a 
        Port class that will be returned when the getPort() is invoked.  The
        returned class is the one acting as a server and therefore must be a
        Portable Object Adapter rather and a simple BULKIO object.
                
        """
        # The classobj generates a class using the following arguments:
        #
        #    name:        The name of the class to generate
        #    bases:       A tuple containing all the base classes to use
        #    dct:         A dictionary containing all the attributes such as
        #                 functions, and class variables
        PortClass = classobj('PortClass',
                             (self.port_type,),
                             {'pushPacket':self._pushPacket,
                              'pushSRI':self._pushSRI})

        # Create a port using the generate Metaclass and return an instance 
        port = PortClass()
        return port._this()