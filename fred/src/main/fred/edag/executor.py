import uuid
from graphlib import TopologicalSorter
from dataclasses import dataclass, field
from typing import Any, Optional

from fred.future.impl import Future
from fred.edag.comp.catalog import CompCatalog
from fred.edag.plan import Plan


@dataclass(frozen=True, slots=True)
class Executor:
    predmap: dict[CompCatalog.NODE.ref, set[CompCatalog.NODE.ref]]
    results: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_plan(cls, plan: Plan, **kwargs) -> "Executor":
        return cls(predmap=plan.as_predmap(**kwargs))
    
    def get_tsort(self) -> TopologicalSorter:
        return TopologicalSorter(self.predmap)
        
    def loop(
            self,
            run_id: str,
            tsort: TopologicalSorter,
            prev_layer: list[list[str]],
            start_with: Optional[dict] = None,
            unrestricted: bool = False,
    ) -> list[list[str]]:
        start_with = start_with or {}
        if not (nodes := tsort.get_ready()):
            return prev_layer
        # You can only get access to results of previous layers unless unrestricted is requested.
        prev_layer_results = self.results[run_id] if unrestricted else {
            key: val
            for key, val in self.results[run_id].items()
            if key in prev_layer[-1]
        }
        curr_layer = []
        for node in nodes:
            parents = [
                parent.name
                for parent in self.predmap.get(node, [])
            ]
            accessible_results = prev_layer_results if unrestricted else {
                key: val
                for key, val in prev_layer_results.items()
                if key in parents
            }
            # Execute node function
            match node.execute(**{**start_with, **accessible_results}):
                case Future() as future:
                    # Can't we just build the whole graph in the future and 'wait_and_resolve' only at the end?
                    # Or at least per layer/generation?
                    self.results[run_id][node.name] = future.wait_and_resolve()
                case present:
                    self.results[run_id][node.name] = present
            # Mark node as done
            tsort.done(node)
            curr_layer.append(node.name)
        prev_layer.append(curr_layer)
        return self.loop(
            run_id=run_id,
            tsort=tsort,
            prev_layer=prev_layer,
            unrestricted=unrestricted,
            start_with={},  # Only availabe during the first layer call
        )

    def execute(self, keep: bool = False, unrestricted: bool = False, start_with: Optional[dict] = None) -> dict:
        from fred.utils.dateops import datetime_utcnow

        run_id = str(uuid.uuid4())
        run_start = datetime_utcnow()
        # Initialize in-memory result storage for this run
        # TODO: Swap the result-store to our fred-keyval implementation
        self.results[run_id] = {}
        # Prepare TopologicalSorter
        tsort = self.get_tsort()
        tsort.prepare()
        # Execute nodes in topological order
        layers = self.loop(
            run_id=run_id,
            tsort=tsort,
            prev_layer=[[]],
            unrestricted=unrestricted,
            start_with=start_with or {},
        )
        return {
            "run_id": run_id,
            "run_start": run_start,
            "run_end": datetime_utcnow(),
            "results": self.results[run_id] if keep else self.results.pop(run_id),
            "layers": layers,
        }
