import enum

from fred.edag.comp.catalog import CompCatalog


class ConnCatalog(enum.Enum):
    PASS = CompCatalog.NODE.ref.auto(
        name="conn:passthrough",
        function=lambda **kwargs: kwargs,
        explode=True,
        inplace=True,
    )
    PASS_PRINT = CompCatalog.NODE.ref.auto(
        name="conn:passthrough_print",
        function=lambda **kwargs: print(kwargs) or kwargs,
        explode=True,
        inplace=True,
    )

    def __call__(self, *args, **kwargs) -> CompCatalog.NODE.ref:
        return self.value.clone(*args, **kwargs)
