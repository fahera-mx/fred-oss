from fred.edag.decorator import NodeDecorator
from fred.edag.comp.catalog import CompCatalog


def test_node_decorator_ops():

    def sample_function(x: int) -> int:
        return x + 1

    decorator = NodeDecorator(name="test_node_decorator_ops", inplace=True)
    wrapped_node = decorator(sample_function)

    assert isinstance(wrapped_node, CompCatalog.NODE.ref)
    assert wrapped_node.name == "test_node_decorator_ops"
    assert wrapped_node.execute(x=5) == 6


def test_node_decorator_syntax():

    @NodeDecorator(name="test_node_decorator_syntax", inplace=True)
    def sample_function(y: int) -> int:
        return y * 2

    assert isinstance(sample_function, CompCatalog.NODE.ref)
    assert sample_function.name == "test_node_decorator_syntax"
    assert sample_function.execute(y=4) == 8


def test_node_decorator_default():
    
    @NodeDecorator
    def sample_function(z: int) -> int:
        return z - 3

    assert isinstance(sample_function, CompCatalog.NODE.ref)
    assert sample_function.name == "sample_function"
    assert sample_function.inplace().execute(z=10) == 7
