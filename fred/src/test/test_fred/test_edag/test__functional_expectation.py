from fred.edag import node
from fred.edag.executor import Executor


def test_linear_dag_2n():

    @node
    def a(start: int) -> int:
        return start + 1

    @node
    def b(a: int) -> int:
        return 2 * a
    
    plan = a >> b
    edag = Executor.from_plan(plan)
    edag.execute(start_with={"start": 1}, unrestricted=True)


def test_linear_dag_3n():

    @node
    def a(start: int) -> int:
        return start + 1

    @node
    def b(a: int) -> int:
        return 2 * a

    @node
    def c(b: int) -> int:
        return b - 3
    
    # Test normal sequential/linear execution
    plan = a >> b >> c
    edag = Executor.from_plan(plan)
    result = edag.execute(start_with={"start": 1}, unrestricted=False)
    assert result["results"]["c"]["c"] == 1

    # Test that it raises an error if trying to access non-accessible results
    @node
    def c(a: int, b: int) -> int:
        return a + b
    
    plan = a >> b >> c
    edag = Executor.from_plan(plan)
    try:
        edag.execute(start_with={"start": 1}, unrestricted=False)
    except TypeError:
        pass
    # Test that it works when unrestricted is True
    result = edag.execute(start_with={"start": 1}, unrestricted=True)
    assert result["results"]["c"]["c"] == 6


def test_passthrough_nonlinear_dag():
    from fred.edag.conn.catalog import ConnCatalog

    @node
    def a(start: int) -> int:
        return start + 1

    @node
    def b(a: int) -> int:
        return 2 * a

    @node
    def c(a: int, b: int) -> int:
        return a + b
    
    plan = a >> (ConnCatalog.PASS() | b) >> c
    edag = Executor.from_plan(plan)
    result = edag.execute(start_with={"start": 1}, unrestricted=False)
    assert result["results"]["c"]["c"] == 6


def test_linear_dag_with_explode():

    @node
    def generate_items(n: int) -> dict[str, int]:
        import string
        return {string.ascii_letters[val]: val for val in range(n)}

    @node
    def sum_items(**kwargs) -> int:
        return sum(kwargs.values())
    
    plan = (~generate_items) >> sum_items
    edag = Executor.from_plan(plan)
    result = edag.execute(start_with={"n": 3})
    assert result["results"]["sum_items"]["sum_items"] == 3


def test_linear_dag_with_iterator_mode():

    @node(inplace=True)
    def elements(n: int) -> list[int]:
        return list(range(n))

    @node(inplace=True)
    def incr(val: int) -> int:
        return val + 1

    plan = elements[...] >> incr
    edag = Executor.from_plan(plan)
    result = edag.execute(start_with={"n": 3})
    assert result["results"]["incr"]["incr"] == [1, 2, 3]

    @node(inplace=True, alias="res")
    def duplicate(val: int) -> int:
        return 2 * val

    @node(inplace=True)
    def addall(res: list[int]) -> int:
        return sum(res)

    plan = elements[...] >> incr[...] >> duplicate.with_output(key="res") >> addall
    edag = Executor.from_plan(plan)
    result = edag.execute(start_with={"n": 3})
    assert result["results"]["addall"]["addall"] == 12
