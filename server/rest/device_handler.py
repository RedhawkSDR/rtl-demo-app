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
