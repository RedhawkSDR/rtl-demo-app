from tornado.testing import main
import unittest

from tests import *

def all():
    return unittest.TestLoader().loadTestsFromModule(__import__(__name__))

if __name__ == '__main__':
    main()