class BadDemodException(Exception):

    def __init__(self, demod):
        Exception.__init__(self, "Bad demodulator '%s'" % demod)
        self.demod = demod

class BadFrequencyException(Exception):

    def __init__(self, frequency):
        Exception.__init__(self, "Bad frequency %s" % frequency)
        self.frequency = frequency