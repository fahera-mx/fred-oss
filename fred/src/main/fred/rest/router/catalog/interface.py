from fred.rest.router.interface import RouterInterface


class RouterCatalogInterface:

    def auto(self, **kwargs) -> RouterInterface:
        return self.value.reference.auto(**kwargs)

    def get_kwargs(self) -> dict:
        # This method can be overridden to provide specific kwargs for router initialization
        return {}
