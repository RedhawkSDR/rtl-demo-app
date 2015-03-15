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
import numpy as np

# third party imports
from tornado import ioloop
from tornado import websocket

logger = logging.getLogger(__name__)

class BulkioHandler(websocket.WebSocketHandler):

    def initialize(self, rtl_app, port_type, subsize=0, APE=1, _ioloop=None):
        self.rtl_app = rtl_app
        self.port_type = port_type
        self.subsize = subsize
        self.APE = APE
        self.blocksize = subsize * APE
        self.buffer =  ''

        # explicit ioloop for unit testing
        if not _ioloop:
            _ioloop = ioloop.IOLoop.instance()

        self._ioloop = _ioloop

    def open(self, ):
        logger.debug('PSD handler for %s open', self.port_type)
        # register event handling
        self.rtl_app.add_stream_listener(self.port_type, self._pushPacket, self._pushSRI)

    def on_message(self, message):
        logger.debug('stream message[%d]: %s', len(message), message)

    def on_close(self):
        logger.debug('PSD handler stream CLOSE')
        try:
            self.rtl_app.rm_stream_listener(self.port_type, self._pushPacket, self._pushSRI)
        except Exception, e:
            logging.exception('Error disconnecting port %s' % self.port_type)

    def _pushSRI(self, SRI):
        self._ioloop.add_callback(self.write_message, 
            dict(hversion=SRI.hversion,
                xstart=SRI.xstart,
                xdelta=SRI.xdelta,
                xunits=SRI.xunits,
                subsize=SRI.subsize if not self.subsize else self.subsize,
                ystart=SRI.ystart,
                ydelta=SRI.ydelta,
                yunits=SRI.yunits,
                mode=SRI.mode,
                streamID=SRI.streamID,
                blocking=SRI.blocking,
                keywords=dict(((kw.id, kw.value.value()) for kw in SRI.keywords))))

    def _pushPacket(self, data, ts, EOS, stream_id):
        # FIXME: need to write ts, EOS and stream id

        logger.error("_pushPacket[%s] received %s bytes.  Buffer %d bytes, blocksize=%d",
                     self.port_type, len(data), len(self.buffer), self.blocksize)
        if not self.blocksize:
            self._ioloop.add_callback(self.write_message, data, binary=True)
        else:
            self.buffer = self.buffer + data
            while len(self.buffer) >= self.blocksize:
                self._ioloop.add_callback(self.write_message, self.buffer[:self.blocksize], binary=True)
                self.buffer = self.buffer[self.blocksize:]
            # FIXME: flush buffer when ending

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(BulkioHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')
