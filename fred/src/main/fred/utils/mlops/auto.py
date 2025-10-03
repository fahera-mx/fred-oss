from typing import Literal, Optional, overload

import torch

from fred.settings import get_environ_variable


def get_device(
        device: Optional[str] = None,
        env_fallback: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str:
    env_default = get_environ_variable(
        env_fallback or "FRD_MLOPS_DEVICE",
        default=None
    )
    # Determine the device to use for model inference
    return device or env_default or default or (
        "cuda" if torch.cuda.is_available() else
        "mps" if torch.backends.mps.is_available() else
        "cpu"
    )


@overload
def get_dtype(
        dtype: Optional[str] = None,
        as_str: Literal[True] = True,
        env_fallback: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str:
    ...


@overload
def get_dtype(
        dtype: Optional[str] = None,
        as_str: Literal[False] = False,
        env_fallback: Optional[str] = None,
        default: Optional[str] = None,
    ) -> torch.dtype:
    ...


def get_dtype(
        dtype: Optional[str] = None,
        as_str: bool = False,
        env_fallback: Optional[str] = None,
        default: Optional[str] = None,
    ) -> str | torch.dtype:
    """
    Determine the data type to use for model inference.
    Args:
        dtype (Optional[str]): The desired data type as a string (e.g., "float16", "float32").
        as_str (bool): If True, return the data type as a string; otherwise, return the torch.dtype object.
        env_fallback (Optional[str]): The name of the environment variable to use as a fallback for the data type. If not provided, defaults to "FRD_MLOPS_DTYPE".
        default (Optional[str]): The default data type to use if neither `dtype` nor the environment variable is set.
    Returns:
        str | torch.dtype: The data type as a string or torch.dtype object.
    """
    # Early exit for string return
    if as_str:
        env_default = get_environ_variable(
            env_fallback or "FRD_MLOPS_DTYPE",
            default=None
        )
        return dtype or env_default or default or (
            "float16" if torch.cuda.is_available() else
            "float32"
        )
    # Return the actual torch.dtype object if not as_str
    return getattr(
        torch,
        get_dtype(dtype=dtype, as_str=True),
        torch.float32,
    )
