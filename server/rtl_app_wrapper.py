# do this as early as possible in your application
from gevent import monkey; monkey.patch_all()

import functools
from tornado import gen, concurrent
from tornado import ioloop
import gevent
import logging
import sys

def _return_future_ioloop(func):
    '''
        Identical to tornado.gen.return_future plus
        thread safety.  Executes the callback in 
        the ioloop thread
    '''
    @functools.partial
    def _exec_func(*args, **kwargs):

        future = concurrent.TracebackFuture()

        try:
         
            io_loop = kwargs.pop('ioloop', None)
            if not io_loop:
                io_loop = ioloop.IOLoop.current()
           
            def _ioloop_callback(val):
                future.set_result(val)

            def _callback(val):
                # set the result in the ioloop thread
                io_loop.add_callback(_ioloop_callback, val)

            func(callback=_callback, *args, **kwargs)
        except Exception:
            future.set_exc_info(sys.exc_info())

        return future

    return _exec_func



def _wrap_background_func(func):

    @functools.wraps(func)
    def _exec_background(*args, **kwargs):
        '''
            Executes a function in a background Greenlet thread
            and returns a Future invoked when the thread completes.
            Useful for IO Bound processes that block.  For CPU
            bound processes consider using celery, DO NOT execute
            CPU Bound tasks in the tornado process!

            io_loop is the optional ioloop used to invoke the callback
            in the processing thread.  This is useful for unit tests
            that do not use the singleton ioloop.  If set to none,
            IOLoop.current() is returned
        '''
        # use explicit ioloop for unit testing
        # Ref: https://github.com/tornadoweb/tornado/issues/663
        io_loop = kwargs.pop('ioloop', None)
        if not io_loop:
            io_loop = ioloop.IOLoop.current()

        # traceback future maintains python stack in exception
        future = concurrent.TracebackFuture()

        def _do_task(*args, **kwargs):
            try:
                rtn = func(*args, **kwargs)
                io_loop.add_callback(future.set_result, rtn)
            except Exception, e:
                logging.debug("Callback exception", exc_info=True)
                io_loop.add_callback(future.set_exc_info, sys.exc_info())


        gevent.spawn(_do_task, *args, **kwargs)
        return future
    return _exec_background

def mk_concurrent_rtl(baseclass):
    '''
        Builds an RTLApp that uses futures for background processes and the
        next_event
    '''
    class RTLApp(baseclass):
        get_survey = _wrap_background_func(baseclass.get_survey)
        set_survey = _wrap_background_func(baseclass.set_survey)
        stop_survey = _wrap_background_func(baseclass.stop_survey)
        get_device = _wrap_background_func(baseclass.get_device)
        #get_available_processing = _wrap_background_func(baseclass.get_available_processing)
        next_event = _return_future_ioloop(baseclass.next_event)
    return RTLApp
