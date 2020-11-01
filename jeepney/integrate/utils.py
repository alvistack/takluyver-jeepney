from itertools import count

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
