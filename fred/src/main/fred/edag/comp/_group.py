from dataclasses import dataclass

from fred.edag.comp.interface import ComponentInterface
from fred.edag.comp._node import Node


@dataclass(frozen=True, slots=True, unsafe_hash=True)
class Group(ComponentInterface):
    nodes: list[Node]  # TODO: let's make this a frozenset instead of a list to ensure immutability
