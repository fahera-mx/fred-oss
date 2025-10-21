import uuid
from graphlib import TopologicalSorter
from dataclasses import dataclass, field
from typing import Any, Optional

from fred.future.impl import Future
from fred.settings import logger_manager
from fred.edag.comp.catalog import CompCatalog
from fred.edag.plan import Plan


logger = logger_manager.get_logger(__name__)


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
            non_destructive_node_explosion: bool = False,
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
            kwargs = {
                **start_with,
                **{
                    arg: val
                    for node_key, node_out in accessible_results.items()
                    for arg, val in node_out.items()
                }
            }
            # Handle iterator mode; if '*' is provided in kwargs, execute node for each item in the iterator
            # and collect results in a list.
            # We should 'pop' to simulate 'consuming' the iterator input and avoid passing it to other nodes.
            if (iterator := kwargs.pop("*", None)):
                logger.debug(f"Executor mapping functionality detected: Node '{node.name}' executing in iterator mode.")
                # TODO: https://github.com/fahera-mx/fred-oss/issues/179
                # TODO: Can we consider explotingi the item components?
                node_output = [
                    node.execute(item)
                    for item in iterator
                ]
            else:
                node_output = node.execute(**kwargs)
            # Execute node function
            match node_output:
                case Future() as future:
                    # Can't we just build the whole graph in the future and 'wait_and_resolve' only at the end?
                    # Or at least per layer/generation?
                    output = {node.key: future.wait_and_resolve()}
                case present:
                    output = {node.key: present}
            # We can only explode if  requested and the output result is a dict
            if node._explode and isinstance(output.get(node.key), dict):
                output = {
                    # Keep original output if non-destrictive-explode is requested;
                    # The original key can be overwritten if key collides during explosion.
                    **(output if non_destructive_node_explosion else {}),
                    # Explode keys into the output dict
                    **output[node.key],
                }
            # Store output in results
            self.results[run_id][node.name] = {
                #**self.results[run_id].get(node.name, {}),
                **output,
            }
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
            non_destructive_node_explosion=non_destructive_node_explosion,
        )

    def execute(
            self,
            keep: bool = False,
            unrestricted: bool = False,
            start_with: Optional[dict] = None,
            non_destructive_node_explosion: bool = False,
        ) -> dict:
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
            non_destructive_node_explosion=non_destructive_node_explosion,
        )
        return {
            "run_id": run_id,
            "run_start": run_start,
            "run_end": datetime_utcnow(),
            "results": self.results[run_id] if keep else self.results.pop(run_id),
            "layers": layers,
        }
