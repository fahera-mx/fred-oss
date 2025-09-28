import posixpath
from dataclasses import dataclass

from fred.settings import logger_manager
from fred.worker.runner.model._runner_spec import RunnerSpec
from fred.worker.runner.plugins.interface import PluginInterface
from fred.settings import get_environ_variable

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=True)
class RunpodPlugin(PluginInterface):

    def _execute(
            self,
            spec: RunnerSpec,
            **kwargs
        ):
        """Execute the runner specification on RunPod's serverless platform.
        Args:
            spec (RunnerSpec): The runner specification to execute.
            **kwargs: Additional keyword arguments for RunPod configuration, such as:
                - runpod_key: API key for RunPod.
                - runpod_url: Base URL for RunPod API.
                - runpod_serverless_id: The ID of the serverless function to invoke.
                - runpod_serverless_endpoint: The endpoint to use ('run' or 'runsync').
                - headers: Additional headers to include in the request.
        """
        import requests

        RUNPOD_KEY = (
            kwargs.get("runpod_key")
            or get_environ_variable(name="RUNPOD_KEY", default="")
        )
        RUNPOD_URL = (
            kwargs.get("runpod_url")
            or get_environ_variable(name="RUNPOD_URL", default="https://api.runpod.ai/v2")
        )
        RUNPOD_SERVERLESS_ID = (
            kwargs.get("runpod_serverless_id")
            or get_environ_variable(name="RUNPOD_SERVERLESS_ID", default=None)
        )
        RUNPOD_SERVERLESS_ENDPOINT = (
            # We do expect the specific endpoint to come from kwargs in most cases
            kwargs.get("runpod_serverless_endpoint")
            or get_environ_variable(name="RUNPOD_SERVERLESS_ENDPOINT", default="run")
        )
        if not RUNPOD_KEY:
            raise ValueError("RUNPOD_KEY is required to execute the runner on RunPod.")
        if not RUNPOD_SERVERLESS_ID:
            raise ValueError("RUNPOD_SERVERLESS_ID is required to execute the runner on RunPod.")
        if RUNPOD_SERVERLESS_ENDPOINT not in ["run", "runsync"]:
            # Right now we only support these two endpoints... We might add more in the future.
            # https://docs.runpod.io/serverless/endpoints/send-requests 
            raise ValueError("RUNPOD_SERVERLESS_ENDPOINT must be either 'run' or 'runsync'.")
        target_url = posixpath.join(
            RUNPOD_URL,
            RUNPOD_SERVERLESS_ID,
            RUNPOD_SERVERLESS_ENDPOINT,
        )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {RUNPOD_KEY}",
            **kwargs.get("headers", {}),
        }
        start_event = spec.as_event(drop_id=True)
        response = requests.post(
            url=target_url,
            json=start_event,
            headers=headers,
        )
        return {
            "target_url": target_url,
            "spec_created_at": spec.created_at,
            "status_code": response.status_code,
            "response": response.json(),
            "ok": response.ok,
        }
