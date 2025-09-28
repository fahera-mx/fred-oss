from dataclasses import dataclass

from fred.worker.runner.rest.routers.interface import RouterInterface


class RunnerRouterMethods:

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
        
    def runner_start(self, payload: dict) -> dict:
        from fred.worker.runner.model.catalog import RunnerModelCatalog
        from fred.worker.runner.plugins.catalog import PluginCatalog
        # Determine which plugin to use; default to LOCAL if not specified
        plugin_name: str = payload.pop("plugin", "LOCAL")
        wait_for_exec: bool = payload.pop("wait_for_exec", False)
        # Create the RunnerSpec from the provided payload
        # TODO: Instead on dependening on parsing a dict... Can we implement a base-model to facilitate fast-api validation?
        runner_spec = RunnerModelCatalog.RUNNER_SPEC.value.from_payload(payload=payload)
        # Instantiate the plugin and execute the runner
        plugin = PluginCatalog[plugin_name.upper()]()
        return {
            "runner_id": plugin.execute(runner_spec, wait_for_exec=wait_for_exec).runner_id,
            "queue_slug": runner_spec.queue_slug,
        }


@dataclass(frozen=True, slots=False)
class RunnerRouter(RouterInterface, RunnerRouterMethods):

    def __post_init__(self):
        self.router.add_api_route(
            "/handler_exists",
            self.handler_exists,
            methods=["GET"],
            tags=["Runner"],
            summary="Check if a handler class exists and is a RunnerHandler.",
            response_description="Details about the handler class.",
        )
        self.router.add_api_route(
            "/start",
            self.runner_start,
            methods=["POST"],
            tags=["Runner"],
            summary="Start a runner using the specified plugin.",
            response_description="The ID of the started runner.",
        )
