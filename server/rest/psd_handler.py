import logging
import numpy

# third party imports
from tornado import ioloop
from tornado import websocket

def _floats2bin(flist):
    """
        Converts a list of python floating point values
        to a packed array of IEEE 754 32 bit floating point
    """
    return numpy.array(flist).astype('float32').tostring()

class PSDHandler(websocket.WebSocketHandler):

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
        self._ioloop.add_callback(self.write_message, _floats2bin(data), binary=True)

    def write_message(self, *args, **ioargs):
        # hide WebSocketClosedError because it's very likely
        try:
            super(PSDHandler, self).write_message(*args, **ioargs)
        except websocket.WebSocketClosedError:
            logging.debug('Received WebSocketClosedError. Ignoring')
