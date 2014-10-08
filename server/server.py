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

# system imports
import os,sys
import time

# third party imports
import tornado
from tornado import ioloop

# application imports
from devices import RTL2832U, sim_RX_DIGITIZER

# setup command line options
from rest import SurveyHandler, DeviceHandler, EventHandler, PSDHandler
from rtl_app import AsyncRTLApp

# establish static directory from this module as one up from current
static_dir = os.path.abspath(os.path.join(os.path.dirname(__import__(__name__).__file__), '..', 'static'))
_BASE_URL = r'/rtl'


def get_application(rtl_app, _ioloop=None, debug=False):

    my_application = tornado.web.Application([
        (r"/apps/(.*)/$", IndexHandler),
        (r"/apps/(.*)", tornado.web.StaticFileHandler, {"path": static_dir}),
        (_BASE_URL + r"/survey", SurveyHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
        (_BASE_URL + r"/device", DeviceHandler, dict(rtl_app=rtl_app, ioloop=_ioloop)),
        (_BASE_URL + r"/status", EventHandler, dict(rtl_app=rtl_app, _ioloop=_ioloop)),
        (_BASE_URL + r"/output/psd/narrowband", PSDHandler,
         dict(rtl_app=rtl_app, port_type=rtl_app.PORT_TYPE_NARROWBAND, _ioloop=_ioloop)),
        (_BASE_URL + r"/output/psd/wideband", PSDHandler,
         dict(rtl_app=rtl_app, port_type=rtl_app.PORT_TYPE_WIDEBAND, _ioloop=_ioloop)),
        (_BASE_URL + r"/output/psd/fm", PSDHandler,
         dict(rtl_app=rtl_app, port_type=rtl_app.PORT_TYPE_FM, _ioloop=_ioloop))
    ], debug=debug)

    return my_application


class IndexHandler(tornado.web.RequestHandler):
    def get(self, path):
        index = os.path.join(static_dir, path, "index.html")
        self.render(index)

if __name__ == '__main__':

    from tornado.options import define, options
    # parse the command line
    define("mock", default=False, type=bool, help="Run with the mock application back end")
    define("delay", default=0, type=int, help="Mock delay in milliseconds")
    define("simulate", default=False, type=bool, help="Simulate the RTL device in REDHAWK")
    define("domain", default="REDHAWK_DEV", help="Redhawk domain")
    define("port", default="8888", help="port")
    define("debug", default=False, type=bool, help="Enable Tornado debug mode.  Reloads code")

    tornado.options.parse_command_line()

    domain_args = []
    device = RTL2832U
    if options.simulate:
        device = sim_RX_DIGITIZER

    if options.mock:
        from mock_rtl_app import AsyncRTLApp
        rtlapp = AsyncRTLApp(options.domain, 
                                    delayfunc=lambda f: time.sleep(options.delay))
    else:
        rtlapp = AsyncRTLApp(options.domain, device)
    application = get_application(rtlapp, debug=options.debug)
    application.listen(options.port)

    tornado.ioloop.PeriodicCallback(rtlapp.poll_device_status, 2000).start()
    ioloop.IOLoop.instance().start()
