from dataclasses import dataclass
from fred.worker.runner.rest.routers.interface import RouterInterface


@dataclass(frozen=True, slots=False)
class RunnerRouter(RouterInterface):

    def __post_init__(self):
        self.router.add_api_route(
            "/handler_exists",
            self.handler_exists,
            methods=["GET"],
            tags=["Runner"],
            summary="Check if a handler class exists and is a RunnerHandler.",
            response_description="Details about the handler class.",
        )

    def handler_exists(self, classname: str, classpath: str) -> dict:
        from fred.worker.runner.handler import RunnerHandler
        from fred.worker.interface import HandlerInterface

        result_payload = {
            "handler_classname": classname,
            "handler_classpath": classpath,
            "exists": False,
            "is_runner_handler": False,
            "metadata": {}
        }

        try:
            handler = HandlerInterface.find_handler(
                import_pattern=classpath,
                handler_classname=classname,
            )
            result_payload["is_runner_handler"] = isinstance(handler, RunnerHandler)
            result_payload["exists"] = True
            return result_payload
        except Exception as e:
            result_payload["metadata"]["error"] = str(e)
            return result_payload
