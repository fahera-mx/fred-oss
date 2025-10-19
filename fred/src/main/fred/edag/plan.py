from dataclasses import dataclass, field
from typing import FrozenSet, Tuple, Union

from fred.edag.comp._node import Node
from fred.edag.comp._group import Group
from fred.edag.comp.interface import ComponentInterface


@dataclass(frozen=True, slots=True)
class Plan:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Tuple[Node, Node]] = field(default_factory=list)  # directed edges: (from/src, to/dst)
    heads: list[Node] = field(default_factory=list)  # current entry set of chaining
    tails: list[Node] = field(default_factory=list)  # current exit set of chaining

    @staticmethod
    def empty() -> 'Plan':
        return Plan()

    @classmethod
    def as_plan(cls, other: Union[ComponentInterface, 'Plan']) -> 'Plan':
        match other:
            case Plan() as plan:
                return plan
            case Node():
                return Plan(
                    nodes=[other],
                    edges=[],
                    heads=[other],
                    tails=[other],
                )
            case Group():
                return Plan(
                    nodes=[*other.nodes],
                    edges=[],
                    heads=[*other.nodes],
                    tails=[*other.nodes],
                )
            case _:
                raise TypeError("as_plan expects Node, Group, or Plan")

    def __rshift__(self, other: Union[ComponentInterface, 'Plan']) -> "Plan":
        other_plan = self.as_plan(other)
        # combine edges, nodes, and link tails -> heads (i.e., connect current tails to new heads)
        new_edges = [
            *self.edges,
            *other_plan.edges,
            *(
                (src, dst)
                for src in self.tails
                for dst in other_plan.heads
            ),
        ]
        new_nodes = [*self.nodes, *other_plan.nodes]
        return Plan(
            nodes=new_nodes,
            edges=new_edges,
            heads=self.heads,
            tails=other_plan.tails,
        )

    def as_predmap(self) -> dict[Node, set[Node]]:
        predmap = {n: set() for n in self.nodes}  # Ensure all nodes are keys
        for src, dst in self.edges:
            predmap[dst].add(src)
        return predmap
