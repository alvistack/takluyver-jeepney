from contextlib import contextmanager
from itertools import count

from jeepney import HeaderFields

class MessageFilters:
    def __init__(self):
        self.filters = {}
        self.filter_ids = count()

    def matches(self, message):
        for handle in self.filters.values():
            if handle.rule.matches(message):
                yield handle


class FilterHandle:
    def __init__(self, filters: MessageFilters, rule, queue):
        self._filters = filters
        self._filter_id = next(filters.filter_ids)
        self.rule = rule
        self.queue = queue

        self._filters.filters[self._filter_id] = self

    def close(self):
        del self._filters.filters[self._filter_id]

    def __enter__(self):
        return self.queue

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class ReplyMatcher:
    def __init__(self):
        self._futures = {}

    @contextmanager
    def catch(self, serial, future):
        """Context manager to capture a reply for the given serial number"""
        self._futures[serial] = future

        try:
            yield future
        finally:
            del self._futures[serial]

    def dispatch(self, msg):
        """Dispatch an incoming message which may be a reply

        Returns True if a task was waiting for it, otherwise False.
        """
        rep_serial = msg.header.fields.get(HeaderFields.reply_serial, -1)
        if rep_serial in self._futures:
            self._futures[rep_serial].set_result(msg)
            return True
        else:
            return False

    def drop_all(self, exc: Exception):
        """Throw an error in any task still waiting for a reply"""
        futures, self._futures = self._futures, {}
        for fut in futures.values():
            fut.set_exception(exc)
