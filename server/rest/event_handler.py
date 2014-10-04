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
