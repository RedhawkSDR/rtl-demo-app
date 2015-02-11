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
import logging

# third party imports
import numpy
from tornado import ioloop

from rest.common import RTLAppHandler
from _utils.audio import wav_hdr

class BulkioWavStreamHandler(RTLAppHandler):

  def initialize(self, rtl_app, port_type, _ioloop=None):
    self.rtl_app = rtl_app
    self.port_type = port_type
    self._auto_finish = False

    # explicit ioloop for unit testing
    if not _ioloop:
      _ioloop = ioloop.IOLoop.instance()

    self._ioloop = _ioloop

  def get(self):
    logging.debug('GET handler for %s open', self.port_type)
    self.set_header('Content-Type', 'audio/wav')
    self.set_header('Transfer-Encoding', 'identity')

    self.write(wav_hdr(1,32000,2))

    # register event handling
    self.rtl_app.add_stream_listener(self.port_type, self._pushPacket, None)

  def _pushSRI(self, SRI):
    self._ioloop.add_callback(self.write,
                              dict(hversion=SRI.hversion,
                                   xstart=SRI.xstart,
                                   xdelta=SRI.xdelta,
                                   xunits=SRI.xunits,
                                   subsize=SRI.subsize,
                                   ystart=SRI.ystart,
                                   ydelta=SRI.ydelta,
                                   yunits=SRI.yunits,
                                   mode=SRI.mode,
                                   streamID=SRI.streamID,
                                   blocking=SRI.blocking,
                                   keywords=dict(((kw.id, kw.value.value()) for kw in SRI.keywords))))

  def _pushPacket(self, data, ts, EOS, stream_id):
    # FIXME: need to write ts, EOS and stream id
    self._ioloop.add_callback(self.write_message, data)

  def write_message(self, data):
    #wave = pcm2wav(data, 1, 32000)

    wave = numpy.array(data).astype('int16')

    self.write(wave.tostring())
    self.flush()

