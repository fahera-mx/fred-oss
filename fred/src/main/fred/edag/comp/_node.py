import uuid
from inspect import Signature, signature, Parameter
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

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
            p.kind == Parameter.VAR_KEYWORD
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
    key: str  # Output key
    nfun: NodeFun
    # TODO: let's make the 'params' a frozenset (i.e., frozenparams) instead of a dict to ensure immutability
    params: dict = field(default_factory=dict)
    nid: str = field(default_factory=lambda: str(uuid.uuid4()))
    inplace: bool = False

    def __hash__(self):
        obj = asdict(self)
        obj["nfun"] = self.nfun.__hash__()
        obj["params"] = frozenset((obj.get("params") or {}).keys())  # only hash keys to avoid unhashable values
        return hash(frozenset(obj.items()))

    def clone(self, **kwargs) -> "Node":
        return Node(
            **{
                "name": self.name,
                "key": self.key,
                "nfun": self.nfun,
                "params": self.params,
                "inplace": self.inplace,
                **kwargs,
            },
            nid=str(uuid.uuid4()),  # Must have a new ID
        )

    @classmethod
    def auto(
            cls,
            function: Callable,
            inplace: bool = False,
            name: Optional[str] = None,
            key: Optional[str] = None,
            **params,
    ):
        name = name or getattr(function, "__name__", "undefined")
        return cls(
            name=name,
            key=key or name,
            nfun=NodeFun.auto(function=function),
            inplace=inplace,
            params=params,
        )

    @property
    def fun(self) -> Callable:
        return self.nfun

    def with_output(self, key: str) -> "Node":
        return self.with_alias(alias=self.name, key=key, keep_key=False)

    def with_alias(self, alias: str, key: Optional[str] = None, keep_key: bool = False) -> "Node":
        return self.__class__(
            name=alias,
            key=key or (self.key if keep_key else alias),
            nfun=self.nfun,
            params=self.params,
            inplace=self.inplace,
        )

    def with_params(self, update_key: Optional[str] = None, **params) -> "Node":
        return self.__class__(
            name=self.name,
            nfun=self.nfun,
            key=update_key or self.key,
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
