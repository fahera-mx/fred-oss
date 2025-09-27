import enum

from fred.worker.runner.model._runner_spec import RunnerSpec
from fred.worker.runner.model._request import RunnerRequest
from fred.worker.runner.model._item import RunnerItem
from fred.worker.runner.model._handler import Handler


class RunnerModelCatalog(enum.Enum):
    RUNNER_SPEC = RunnerSpec
    REQUEST = RunnerRequest
    HANDLER = Handler
    ITEM = RunnerItem

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)
