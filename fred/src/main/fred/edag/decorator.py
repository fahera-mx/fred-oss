from typing import Callable, Optional

from fred.edag.comp.catalog import CompCatalog


class NodeDecorator:
    """Decorator to create Node instances from functions.
    Can be used with or without parameters.

    Example usage:

    @NodeDecorator
    def my_function(...):
        ...
    or
    @NodeDecorator(name="example", param1=value1, param2=value2)
        def my_function(...):
    """

    def __new__(cls, func: Optional[Callable] = None, **kwargs):
        if not func:
            # Create an instance of NodeDecorator to hold kwargs until __call__ is invoked
            instance = super(NodeDecorator, cls).__new__(cls)
            instance.kwargs = kwargs
            return instance
        # Return a Node instance directly if func is provided
        return CompCatalog.NODE.ref.auto(
            function=func,
            **kwargs,
        )

    def __init__(self, func: Optional[Callable] = None, **kwargs):
        self.func = func
        self.kwargs = kwargs

    def __call__(self, func: Callable, **kwargs) -> CompCatalog.NODE.ref:
        self.func = func
        self.kwargs = {**self.kwargs, **kwargs}
        return self.get_node()

    def get_node(self, **kwargs) -> CompCatalog.NODE.ref:
        return CompCatalog.NODE.ref.auto(
            function=self.func,
            **{
                **self.kwargs,
                **kwargs,
            },
        )
