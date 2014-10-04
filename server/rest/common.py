
# third party imports
from tornado import web

class RTLAppHandler(web.RequestHandler):

    def initialize(self, rtl_app, ioloop=None):
        self.rtl_app = rtl_app
        # explicit ioloop for unit testing
        self.ioloop = ioloop
