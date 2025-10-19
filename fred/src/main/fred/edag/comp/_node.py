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
    
    def __hash__(self):
        return hash((
            self.inner,
            tuple(self.signature.parameters.items()),
        ))
