from __future__ import print_function

import unittest

from tornado import gen, ioloop

from ..opentracing_mock import MockTracer
from ..utils import get_logger
from ..utils_tornado import run_until


logger = get_logger(__name__)


class TestTornado(unittest.TestCase):
    def setUp(self):
        self.tracer = MockTracer()
        self.loop = ioloop.IOLoop.current()

    def test_main(self):
        # Create a Span and use it as parent of a pair of subtasks.
        parent_span = self.tracer.start_span('parent')
        self.submit_subtasks(parent_span)

        run_until(self.loop, lambda: len(self.tracer.finished_spans) >= 2)
        self.loop.start()

        # Late-finish the parent Span now.
        parent_span.finish()

        spans = self.tracer.finished_spans
        self.assertEqual(len(spans), 3)
        self.assertEqual(spans[0].operation_name, 'task1')
        self.assertEqual(spans[1].operation_name, 'task2')
        self.assertEqual(spans[2].operation_name, 'parent')

        for i in range(2):
            self.assertEquals(spans[i].context.trace_id,
                              spans[-1].context.trace_id)
            self.assertEquals(spans[i].parent_id,
                              spans[-1].context.span_id)
            self.assertTrue(spans[i].finish_time <= spans[-1].finish_time)

    # Fire away a few subtasks, passing a parent Span whose lifetime
    # is not tied at all to the children.
    def submit_subtasks(self, parent_span):
        @gen.coroutine
        def task(name, interval):
            logger.info('Running %s' % name)
            with self.tracer.start_span(name, child_of=parent_span):
                yield gen.sleep(interval)

        self.loop.add_callback(task, 'task1', 0.1)
        self.loop.add_callback(task, 'task2', 0.3)
