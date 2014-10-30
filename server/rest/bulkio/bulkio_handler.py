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
from tornado import ioloop
from tornado import websocket

class BulkioHandler(websocket.WebSocketHandler):

    def initialize(self, rtl_app, port_type, _ioloop=None):
        self.rtl_app = rtl_app
        self.port_type = port_type

        # explicit ioloop for unit testing
        if not _ioloop:
            _ioloop = ioloop.IOLoop.instance()

        self._ioloop = _ioloop

    def open(self, ):
        logging.debug('PSD handler for %s open', self.port_type)
        # register event handling
        self.rtl_app.add_stream_listener(self.port_type, self._pushPacket, self._pushSRI)

    def on_message(self, message):
        logging.debug('stream message[%d]: %s', len(message), message)

    def on_close(self):
        logging.debug('PSD handler stream CLOSE')
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
        self._ioloop.add_callback(self.write_message, data, binary=True)

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(BulkioHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')
