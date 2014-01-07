from __future__ import division
import os, sys
import logging
import logging.handlers
from collections import deque
import threading
import multiprocessing
from Queue import Empty
import datetime

class GeneratorWorker(multiprocessing.Process):
    name = 'GeneratorWorker'
    stopping = False

    def __init__(self, num, q1, q2):
        # Logger already setup by config, just get an instance
        logger = logging.getLogger('eventgen')
        globals()['logger'] = logger

        from eventgenconfig import Config
        globals()['c'] = Config()

        logger.debug("Starting GeneratorWorker")

        self._pluginCache = { }

        self.num = num
        c.generatorQueue = q1
        c.outputQueue = q2

        multiprocessing.Process.__init__(self)

    def __str__(self):
        """Only used for debugging, outputs a pretty printed representation of this output"""
        # Eliminate recursive going back to parent
        temp = dict([ (key, value) for (key, value) in self.__dict__.items() if key != '_c'])
        # return pprint.pformat(temp)
        return ""

    def __repr__(self):
        return self.__str__()

    def run(self):
        # TODO hide this behind a config setting
        if True:
            import cProfile
            globals()['threadrun'] = self.real_run
            cProfile.runctx("threadrun()", globals(), locals(), "eventgen_generatorworker_%s" % self.num)
        else:
            self.real_run()

    def real_run(self):
        while not self.stopping:
            try:
                # Grab item from the queue to generate, grab an instance of the plugin, then generate
                sample, count, earliest, latest = c.generatorQueue.get(block=True, timeout=1.0)
                if sample.name in self._pluginCache:
                    plugin = self._pluginCache[sample.name]
                    plugin.updateSample(sample)
                else:
                    plugin = c.getPlugin('generator.'+sample.generator)(sample)
                    self._pluginCache[sample.name] = plugin
                logger.info("GeneratorWorker %d generating %d events from '%s' to '%s'" % (self.num, count, \
                            datetime.datetime.strftime(earliest, "%Y-%m-%d %H:%M:%S"), \
                            datetime.datetime.strftime(latest, "%Y-%m-%d %H:%M:%S")))
                plugin.gen(count, earliest, latest)
            except Empty:
                # Queue empty, do nothing... basically here to catch interrupts
                pass

    def stop(self):
        self.stopping = True

def load():
    return GeneratorWorker