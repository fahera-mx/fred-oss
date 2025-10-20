from inspect import Signature, signature, _ParameterKind
from dataclasses import dataclass, field, asdict
from typing import Callable

from fred.edag.comp.interface import ComponentInterface


@dataclass(frozen=True, slots=True)
class NodeFun:
    inner: Callable
    signature: Signature

    @classmethod
    def auto(cls, function: Callable) -> "NodeFun":
        return cls(
            inner=function,
            signature=signature(function),
        )

    def validate_parameter_compliance(self, *args, **kwargs) -> dict:
        # Determine if the signature accepts **kwargs
        var_kwargs = any(
            p.kind == _ParameterKind.VAR_KEYWORD
            for p in self.signature.parameters.values()
        )
        # Validate keywords against signature if not accepting **kwargs
        clean_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in self.signature.parameters
        } if not var_kwargs else kwargs
        # Bind arguments to signature
        bound = self.signature.bind_partial(*args, **clean_kwargs)
        bound.apply_defaults()
        # Return the bound arguments as a dictionary
        return {
            k: v
            for k, v in bound.arguments.items()
        }

    def __call__(self, *args, **kwargs):
        params = self.validate_parameter_compliance(*args, **kwargs)
        return self.inner(**params)
    
    def __name__(self):
        return getattr(self.inner, "__name__", "undefined")

    def __hash__(self):
        return hash((
            self.inner,
            tuple(self.signature.parameters.items()),
        ))


@dataclass(frozen=True, slots=True)
class Node(ComponentInterface):
    name: str
    nfun: NodeFun
    # TODO: let's make the 'params' a frozenset (i.e., frozenparams) instead of a dict to ensure immutability
    params: dict = field(default_factory=dict)
    inplace: bool = False

    def __hash__(self):
        obj = asdict(self)
        obj["nfun"] = self.nfun.__hash__()
        obj["params"] = frozenset((obj.get("params") or {}).keys())  # only hash keys to avoid unhashable values
        return hash(frozenset(obj.items()))

    @classmethod
    def auto(
            cls,
            function: Callable,
            inplace: bool = False,
            **params,
    ):
        name = params.pop("name", None) or getattr(function, "__name__", "undefined")
        return cls(
            name=name,
            nfun=NodeFun.auto(function=function),
            inplace=inplace,
            params=params,
        )

    @property
    def fun(self) -> Callable:
        return self.nfun

    def with_alias(self, alias: str) -> "Node":
        return self.with_params(alias=alias)

    def with_params(self, **params) -> "Node":
        return self.__class__(
            name=self.name,
            nfun=self.nfun,
            params={
                **self.params,
                **params,
            },
            inplace=self.inplace,
        )

    def execute(self, **kwargs):
        params = {
            **self.params,
            **kwargs
        }
        if self.inplace:
            return self.fun(**params)
        from fred.future.impl import Future
        return Future(self.fun, **params)
