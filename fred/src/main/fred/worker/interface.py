import time
from typing import Callable, Optional
from dataclasses import dataclass, field

from fred.utils.dateops import datetime_utcnow
from fred.settings import (
    get_environ_variable,
    logger_manager,
)

logger = logger_manager.get_logger(name=__name__)


@dataclass(frozen=True, slots=False)
class HandlerInterface:
    """Base interface for handling events in a worker environment.
    
    This class provides a structure for processing events with metadata tracking.
    Subclasses should implement the `handler` method to define specific event processing logic.
    
    Considerations: This interface is designed to be extended for various worker implementations, starting with Runpod.

    Attributes:
        context (dict): A dictionary to hold contextual information for the handler; this can be modified as needed.
        metadata (dict): A dictionary to track metadata about the handler's operations.
    """
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    custom_actions: dict = field(default_factory=dict)

    def __post_init__(self):
        self.metadata["handler_created_at"] = datetime_utcnow().isoformat()

    @classmethod
    def find_handler(
            cls,
            import_pattern: str,
            handler_classname: str,
            **init_kwargs,
    ) -> 'HandlerInterface':
        import importlib

        # Dynamically import the handler class
        handler_module = importlib.import_module(import_pattern)
        handler_cls = getattr(handler_module, handler_classname)
        # Ensure the handler class exists and is a subclass of HandlerInterface
        if not handler_cls or not issubclass(handler_cls, cls):
            logger.error(f"Handler class '{handler_classname}' not found or is not a subclass of HandlerInterface: {handler_cls}")
            raise ValueError(f"Handler '{handler_classname}' not found in module '{import_pattern}' or is not a subclass of HandlerInterface.")
        kwargs = {
            "metadata": {
                "handler_found_at": datetime_utcnow().isoformat()
            },
            **init_kwargs,
        }
        return handler_cls.with_custom_actions(**kwargs)
    
    @classmethod
    def with_custom_actions(cls, actions: Optional[dict] = None, **init_kwargs) -> 'HandlerInterface':
        return cls(**init_kwargs).register_actions(actions=actions)

    def register_actions(self, actions: Optional[dict] = None) -> 'HandlerInterface':
        """Register multiple custom actions from a dictionary. You can chain this method after instantiation.
        Consider extending this method on child classes to register additinal custom actions:

        class MyHandler(HandlerInterface):
            
            def my_custom_action_method(self, **kwargs) -> dict:
                return {"status": "custom action executed", **kwargs}

            def register_actions(self, actions: Optional[dict] = None) -> 'HandlerInterface':
                # Call the parent method to register base actions
                super().register_actions(actions=actions)
                # Register additional custom actions specific to MyHandler
                self.register_custom_action(
                    action_name="my_custom_action",
                    action_callable=self.my_custom_action_method
                )
                return self

        Args:
            actions (dict): A dictionary where keys are action names and values are callables.
        Returns:
            HandlerInterface: The instance itself to allow method chaining.
        """
        # Register provided custom actions as arguments
        for action_name, action_callable in (actions or {}).items():
            self.register_custom_action(action_name=action_name, action_callable=action_callable)
        # Example custom action, just for demonstration purposes (e.g., a ping action)
        self.register_custom_action(
            action_name="ping",
            action_callable=lambda **kwargs: {
                "reply": "pong",
                "reply_at": datetime_utcnow().isoformat(),
                **kwargs,
            }
        )
        return self

    def register_custom_action(self, action_name: str, action_callable: Callable, ignore_if_exists: bool = False):
        """Register a custom action that can be invoked via the `fred_worker_action` key in the event payload.
        Args:
            action_name (str): The name of the custom action to register.
            action_callable (Callable): A callable (function or method) that implements the action.
            ignore_if_exists (bool): If True, will not overwrite an existing action with the same name.
        Raises:
            ValueError: If the action_callable is not callable.
        """
        if not callable(action_callable):
            raise ValueError(f"The action_callable must be a callable function or method: {type(action_callable)}")
        if action_name in self.custom_actions:
            if ignore_if_exists:
                logger.info(f"Custom action '{action_name}' already exists; ignoring as per flag.")
                return
            logger.warning(f"Overwriting existing custom action: '{action_name}'")
        self.custom_actions[action_name] = action_callable


    def telemetry(self, include_modules: bool = False) -> dict:
        from fred.utils.runtime import RuntimeInfo
        runtime_info = RuntimeInfo.auto()
        return runtime_info.to_dict(
            exclude_modules=not include_modules
        )

    def handler(self, payload: dict) -> Optional[dict]:
        logger.warning("Handler method not implemented.")
        return payload

    @property
    def metadata_prepared(self) -> dict:
        if not int(get_environ_variable("FRD_ENFORCE_METADATA_SERIALIZATION", default="0")):
            return self.metadata
        import json
        # Ensure serializability
        # TODO: Allow custom serialization methods
        metadata_serialized = json.dumps(self.metadata, default=str)
        return json.loads(metadata_serialized)

    def run(self, event: dict) -> dict:
        """Process an incoming event and return a structured response.
        The event is expected to be a dictionary with at least an 'id' and 'input' keys.
        The 'input' key should contain the payload to be processed.
        Args:
            event (dict): The incoming event containing 'id' and 'input'.
        Returns:
            dict: A structured response containing the result of processing the event.    
        """
        # Extract payload and event ID
        payload = event.get("input", {})
        job_event_identifier = event.get("id")
        # Update metadata for this run instance and timing information
        self.metadata["run_seq"] = self.metadata.get("run_seq", 0) + 1
        started_at = datetime_utcnow().isoformat()
        start_time = time.perf_counter()
        # Default response values
        ok = True
        response = None
        # Determine action based on 'fred_worker_action' in payload
        match (worker_action := payload.pop("fred_worker_action", "handler")):
            case "telemetry":
                # Collect and return telemetry data
                logger.debug("Standard telemetry action requested.")
                response = self.telemetry()
            case "handler":
                # Process the payload using the handler method
                logger.debug("Standard handler action requested.")
                try:
                    response = self.handler(payload=payload)
                except Exception as e:
                    ok = False
                    logger.error(f"Error processing handler for event {job_event_identifier}: {e}")
                    response = {
                        "error": str(e)
                    }
            case action if isinstance(action, str):
                # Handle custom actions defined in the custom_actions dictionary
                logger.info(f"Custom fred_worker_action '{action}' received.")
                match self.custom_actions.get(action):
                    case None:
                        ok = False
                        response = {
                            "error": f"Custom action '{action}' not found."
                        }
                    case custom_action_function if callable(custom_action_function):
                        try:
                            response = custom_action_function(**payload)
                        except Exception as e:
                            ok = False
                            logger.error(f"Error processing custom action '{action}' for event {job_event_identifier}: {e}")
                            response = {
                                "error": str(e)
                            }
                    case _:
                        ok = False
                        response = {
                            "error": f"Custom action '{action}' is not callable."
                        }
            case _:
                # Handle invalid action types
                logger.error(f"Invalid fred_worker_action type received: {type(worker_action)}")
                ok = False
                response = {
                    "error": "Invalid fred_worker_action type."
                }
        return {
            "ok": ok,
            "id": job_event_identifier,
            "started_at": started_at,
            "duration": time.perf_counter() - start_time,
            "worker_action": worker_action,
            "response": response,
            "metadata": self.metadata_prepared,
        }
