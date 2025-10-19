import enum

from fred.edag.comp.interface import ComponentInterface
from fred.edag.comp._group import Group
from fred.edag.comp._node import Node
from fred.edag.plan import Plan


class PlanCompositionMixin:

    def __rshift__(self, other: ComponentInterface | Plan) -> Plan:
        left = Plan.as_plan(self)
        right = Plan.as_plan(other)
        return left >> right


class CompCatalog(enum.Enum):
    NODE = type("Node", (Node, PlanCompositionMixin), {})
    GROUP = type("Group", (Group, PlanCompositionMixin), {})

    @property
    def ref(self) -> type[ComponentInterface]:
        return self.value

    def __call__(self, *args, **kwargs) -> ComponentInterface:
        return self.value(*args, **kwargs)
