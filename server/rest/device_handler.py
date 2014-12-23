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
import json
from tornado import gen

from common import RTLAppHandler

class DeviceHandler(RTLAppHandler):

    @gen.coroutine
    def get(self):
        logging.info("Device GET")
        try:
            device = yield self.rtl_app.get_device()
            self.write(device)
        except Exception:
            logging.exception("Error getting device")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred'))
        logging.info("Survey DELETE End")

    @gen.coroutine
    def put(self):
        logging.info("Device PUT")
        try:
            data = json.loads(self.request.body)
        except Exception:
            logging.exception('Unable to parse json: "%s"', self.request.body)
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=self.request.body))
            return

        if not "simulation" in data:
            logging.error('Expecting field "simulation" in json: "%s"', self.request.body)
            self.set_status(500)
            self.write(dict(success=False,
                            error="Expecting field 'simulation'",
                            request=self.request.body))
            return

        try:
            use_simulation=data['simulation']
            logging.debug("Setting simulation to %s", use_simulation)
            yield self.rtl_app.set_simulation(use_simulation)
            self.write(dict(success=True, simulation=use_simulation))
        except Exception, e:
            logging.exception("Error setting simulation mode", e)
            self.set_status(500)
            self.write(dict(success=False,
                            error='Error setting simulation mode',
                            message=e.message,
                            request=self.request.body))