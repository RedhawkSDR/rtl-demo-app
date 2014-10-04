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
                                                   demod=data['processing'])
            logging.info("post CALLBACK")
            self.write(dict(success=True,
                            status=dict(frequency=survey['frequency'],
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
                                        processing=survey['demod'])))
        except Exception:
            logging.exception("Error stopping survey")
            self.set_status(500)
            self.write(dict(success=False,
                            error='An unknown system error occurred'))

        logging.info("Survey DELETE End")
