from fred.rest.router.interface import RouterInterfaceMixin
from fred.rest.router.endpoint import RouterEndpointAnnotation


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

    @RouterEndpointAnnotation.set(
        path="/passthrough",
        methods=["POST"],
        summary="Passthrough POST endpoint",
        description="An endpoint that returns all received parameters.",
    )
    def passthrough(self, **kwargs) -> dict:
        return kwargs
