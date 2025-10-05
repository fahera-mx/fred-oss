import os
import json
from dataclasses import dataclass, field
from typing import Optional



def load_policy(filename: str, path: Optional[str] = None, **kwargs) -> dict:
    path = path or os.path.join(os.path.dirname(__file__), "templates")
    filepath = os.path.join(path, filename)
    # Read the policy file as a string
    with open(filepath, "r", encoding="utf-8") as file:
        policy_str = file.read()
    # Replace placeholders in the policy with actual values from kwargs
    for param_key, param_val in kwargs.items():
        param_ref = "${{param_key}}".replace("param_key", param_key)
        policy_str = policy_str.replace(param_ref, param_val)
    return json.loads(policy_str)


@dataclass(frozen=True, slots=True)
class MinioPolicyLoader:
    title: str
    filename: str
    requires: list[str] = field(default_factory=list)

    def load(self, path: Optional[str] = None, **kwargs) -> dict:
        if (missing := set(self.requires) - set(kwargs.keys())):
            raise ValueError(f"Missing required parameters for policy '{self.filename}': {missing}")
        return load_policy(filename=self.filename, path=path, **kwargs)
