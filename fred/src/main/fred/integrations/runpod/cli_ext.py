from fred.worker.interface import HandlerInterface
from fred.cli.interface import IntegrationExtCLI
from fred.settings import logger_manager


logger = logger_manager.get_logger(name=__name__)


class RunPodExt(IntegrationExtCLI):

    def get_handler_instance(self, import_pattern: str, handler_classname: str) -> HandlerInterface:
        return HandlerInterface.find_handler(
            import_pattern=import_pattern,
            handler_classname=handler_classname,
        )

    def execute_local(self, import_pattern: str, handler_classname: str, **kwargs) -> dict:
        payload = kwargs.pop("payload", {})
        handler = self.get_handler_instance(
            import_pattern=import_pattern,
            handler_classname=handler_classname,
        )
        return handler.run(
            event={
                "id": "local-exec",
                "input": payload,
            }
        )

    def execute(self, import_pattern: str, handler_classname: str, local: bool = False, **kwargs):
        # Early exit and redirect to local execution when specified.
        if local:
            return self.execute_local(import_pattern, handler_classname, **kwargs)
        
        # Lazy import to avoid dependency issues when not using RunPod
        import runpod  # type: ignore
        
        logger.info(f"Starting RunPod serverless with handler '{handler_classname}' from '{import_pattern}'.")
        handler = self.get_handler_instance(
            import_pattern=import_pattern,
            handler_classname=handler_classname,
        )
        runpod.serverless.start(
            {
                "handler": handler.run,
                **kwargs,
            }
        )
