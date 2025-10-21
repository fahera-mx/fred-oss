from fred.edag.comp.catalog import CompCatalog
from fred.edag.plan import Plan


def test_as_plan():
    plan = Plan.empty()
    assert Plan.as_plan(plan) is plan

    node = CompCatalog.NODE.ref.auto(lambda: None)
    plan_from_node = Plan.as_plan(node)
    assert isinstance(plan_from_node, Plan)
    assert plan_from_node.nodes == [node]
