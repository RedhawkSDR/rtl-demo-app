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
