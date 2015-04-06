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
'''
   Survey Request Handler.

   A RESTful RequestHandler for RTL Application Demo
'''
# system imports
import json
import logging

# third party imports
from tornado import gen

# application imports
from rtl_app import BadDemodException, BadFrequencyException, DeviceUnavailableException
from common import RTLAppHandler

class SurveyHandler(RTLAppHandler):

    @gen.coroutine
    def get(self):
        logging.info("Survey GET")
        try:
            processing = self.rtl_app.get_available_processing()
            survey = yield self.rtl_app.get_survey()

            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
                                        demod_if=survey['demod_if'],
                                        processing=survey['demod']),
                            availableProcessing=processing))

        except Exception:
            logging.exception("Error getting survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=self.request.body))

    @gen.coroutine
    def post(self):
        logging.debug("Survey POST")
        try:
            data = json.loads(self.request.body)
        except Exception:
            logging.exception('Unable to parse json: "%s"', self.request.body),
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=self.request.body))
            return


        try:
            survey = yield self.rtl_app.set_survey(frequency=data['frequency'],
                                                   demod_if=data.get('demod_if', 0),
                                                   demod=data['processing'])
            logging.info("post CALLBACK")
            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
                                        demod_if=survey['demod_if'],
                                        processing=survey['demod'])))
        except BadFrequencyException:
            self.set_status(400)
            self.write(dict(success=False,
                            error='Frequency is invalid',
                            request=data))
        except BadDemodException:
            self.set_status(405)
            self.write(dict(success=False,
                            error="'%s' is not a valid processor" % data['processing'],
                            request=data))
        except DeviceUnavailableException:
            self.set_status(400)
            self.write(dict(success=False,
                            error="RTL device is not available",
                            request=data))
        except Exception:
            logging.exception("Error setting survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred',
                            request=data))

    @gen.coroutine
    def delete(self):
        logging.info("Survey DELETE")
        try:
            survey = yield self.rtl_app.stop_survey()
            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
                                        demod_if=survey['demod_if'],
                                        processing=survey['demod'])))
        except Exception:
            logging.exception("Error stopping survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred'))

        logging.info("Survey DELETE End")
