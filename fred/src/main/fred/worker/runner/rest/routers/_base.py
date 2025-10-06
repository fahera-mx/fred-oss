from dataclasses import dataclass

from fred.rest.router.interface import RouterInterfaceMixin
from fred.rest.router.endpoint import RouterEndpointAnnotation

@dataclass(frozen=True, slots=True)
class RouterBaseMixin(RouterInterfaceMixin):
    
    @RouterEndpointAnnotation.set(
        path="/",
        methods=["GET"],
        summary="Base endpoint",
        description="A simple base endpoint to check service availability."
    )
    def base(self, include_telemetry: bool = False, **kwargs) -> dict:
        if include_telemetry:
            from fred.utils.runtime import RuntimeProfilingSnapshot
            kwargs["telemetry"] = RuntimeProfilingSnapshot.auto().to_dict()
        return {
            "ok": True,
            **kwargs
        }
