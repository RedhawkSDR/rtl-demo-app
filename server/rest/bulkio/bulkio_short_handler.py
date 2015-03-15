#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK server.
#
# REDHAWK server is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK server is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
import numpy

from bulkio_handler import BulkioHandler

class BulkioShortHandler(BulkioHandler):

    @staticmethod
    def __shorts2bin(flist):
      """
          Converts a list of python floating point values
          to a packed array of IEEE 754 32 bit floating point
      """
      return numpy.array(flist).astype('int16').tostring()

    def _pushPacket(self, data, ts, EOS, stream_id):
        super(BulkioShortHandler, self)._pushPacket(self.__shorts2bin(data), ts, EOS, stream_id)

