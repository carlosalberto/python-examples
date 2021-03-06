from __future__ import print_function

from concurrent.futures import ThreadPoolExecutor
import time
import unittest

from ..opentracing_mock import MockTracer


class TestThreads(unittest.TestCase):
    def setUp(self):
        self.tracer = MockTracer()
        self.executor = ThreadPoolExecutor(max_workers=3)

    def test_main(self):
        # Create a Span and use it as parent of a pair of subtasks.
        parent_span = self.tracer.start_span('parent')
        self.submit_subtasks(parent_span)

        # Wait for the threadpool to be done.
        self.executor.shutdown(True)

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
        def task(name, interval):
            with self.tracer.start_span(name, child_of=parent_span):
                time.sleep(interval)

        self.executor.submit(task, 'task1', 0.1)
        self.executor.submit(task, 'task2', 0.3)
