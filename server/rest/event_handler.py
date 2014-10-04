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
from tornado import ioloop, websocket

class EventHandler(websocket.WebSocketHandler):

    def initialize(self, rtl_app, _ioloop=None):
        self.rtl_app = rtl_app

        # explicit ioloop for unit testing
        if not _ioloop:
            _ioloop = ioloop.IOLoop.instance()

        self.ioloop = _ioloop

    def open(self):
        logging.debug('Event handler open')
        # register event handling
        self.rtl_app.add_event_listener(self._post_event)

    def on_message(self, message):
        logging.debug('stream message[%d]: %s', len(message), message)

    def on_close(self):
        logging.debug('Stream CLOSE')
        self.rtl_app.rm_event_listener(self._post_event)

    def _post_event(self, event):
        # if connection still open, post the next event
        #if self.ws_connection:
        self.ioloop.add_callback(self.write_message, event)
