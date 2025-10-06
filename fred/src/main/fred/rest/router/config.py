from dataclasses import dataclass

from fred.rest.router.interface import RouterInterface, RouterInterfaceMixin


@dataclass(frozen=True, slots=True)
class RouterConfig:
    prefix: str
    other: dict

    @classmethod
    def auto(cls, prefix: str = "", **kwargs) -> "RouterConfig":
        return cls(
            prefix=prefix,
            other=kwargs,
        )

    def get_applied_configs(self, router_class: type[RouterInterface]) -> "AppliedRouterConfig":
        return AppliedRouterConfig(
            reference=router_class,
            config=self,
        )

    def __call__(self, apply: type[RouterInterfaceMixin]) -> "AppliedRouterConfig":
        router_classname = f"Router{apply.__name__}"
        return self.get_applied_configs(
            router_class=type(router_classname, (RouterInterface, apply, ), {})
        )
    
    def get_configs(self) -> dict:
        return {
            "prefix": self.prefix,
            **self.other,
        }


@dataclass(frozen=True, slots=True)
class AppliedRouterConfig:
    reference: type[RouterInterface]
    config: RouterConfig
