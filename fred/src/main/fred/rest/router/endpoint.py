import os
from dataclasses import dataclass, field
from typing import Callable, Optional

from fastapi import Request

from fred.settings import logger_manager

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RouterEndpointConfig:
    path: Optional[str] = None
    methods: list[str] = field(default_factory=lambda: ["GET"])
    configs: dict = field(default_factory=dict)

    @classmethod
    def auto(cls, **kwargs) -> "RouterEndpointConfig":
        return cls(
            path=kwargs.pop("path", None),
            methods=(
                kwargs.pop("methods", None)
                or ["GET"]
            ),
            configs=kwargs
        ) 


@dataclass(frozen=True, slots=False)
class RouterEndpoint:
    function: Callable
    configs: RouterEndpointConfig

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def get_path(self, overwrite: Optional[str] = None) -> str:
        fname = self.function.__name__
        return (
            overwrite
            or self.configs.path
            or logger.debug(f"Missing 'path' definition, defaulting to function name: {fname}")
            or os.path.join("/", fname)
        )

    def route_config(self, path: Optional[str] = None) -> dict:
        return {
            "path": self.get_path(overwrite=path),
            "methods": self.configs.methods,
            **self.configs.configs,
        }

# Here are a couple of reference to understand why this class is needed:
# https://stackoverflow.com/questions/2365701/decorating-class-methods-how-to-pass-the-instance-to-the-decorator/3296318#3296318
# https://stackoverflow.com/questions/75409483/why-do-i-get-missing-required-argument-self-when-using-a-decorator-written-as
@dataclass(frozen=True, slots=True)
class RouterEndpointAnnotation(RouterEndpoint):
    
    @classmethod
    def set(cls, **kwargs) -> Callable:
        config = RouterEndpointConfig.auto(**kwargs)
        return lambda function: cls(function=function, configs=config)

    def __get__(self, other_instance, other_class) -> RouterEndpoint:
        # Create a partial function that binds the instance (other) to the method.
        # This method was originally implemented using the following approaches:
        # - function = functools.partial(self.function, other)
        # - function = lambda payload: self.function(other, **payload)
        # - function = functools.wraps(self.function)(lambda *args, **kwargs: self.function(other, *args, **kwargs)) 
        # However, these approaches did not work well with FastAPI's async handling and request parsing
        # since the dynamic lambda attributes were not being recognized properly by FastAPI.
        # The current implementation defines an async closure that correctly calls the inner function
        # and retrieves the parameters directly from the Request object.
        # For more info on how to use the request object, see:
        # - https://fastapi.tiangolo.com/advanced/using-request-directly/#use-the-request-object-directly
        # - https://stackoverflow.com/questions/67636088/how-to-access-request-object-in-router-function-using-fastapi
        # - https://www.starlette.dev/requests/
        async def closure(request: Request):
            params = {
                **request.headers,
                **request.path_params,
                **request.query_params,
            }
            try:
                if request.method in ("POST", "PUT", "PATCH"):
                    params.update(await request.json())
            except Exception:
                pass
            # Since the annotation is usually applied to methods within a class,
            # in most cases the 'other_instance' will be 'None'; therefore using 'other_class'
            # should allow accessing the shared-class level state (e.g., runner_backend).
            return self.function(other_class, **params)
        return RouterEndpoint(
            function=closure,
            configs=self.configs
        )
