import io
import base64
from typing import Optional

from PIL.Image import Image

from fred.settings import logger_manager

logger = logger_manager.get_logger(__name__)


def save_image_to_path(image: Image, path: str) -> None:
    """
    Save a PIL Image to the specified file path.

    Args:
        image (Image): The PIL Image to save.
        path (str): The file path where the image will be saved.
    """
    image.save(path)


def image_to_b64(image: Image, format: Optional[str] = None) -> str:
    """
    Convert a PIL Image to a base64-encoded string.
    Args:
        image (Image): The PIL Image to convert.
        format (Optional[str]): The format to use for encoding (e.g., "PNG", "JPEG"). Defaults to "PNG" if None.
    Returns:
        str: The base64-encoded image string.
    """
    # Convert the image to a base64 string
    buffer = io.BytesIO()
    image.save(buffer, format=format or "PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_image_from_b64(image_b64: str) -> Image:
    """Load an image from a base64-encoded string.
    Args:
        image_b64 (str): The base64-encoded image string.
    Returns:
        Image: The loaded PIL Image.
    """
    import PIL.Image
    # Decode the base64 string to bytes
    image_data = base64.b64decode(image_b64)
    # Open the image using PIL
    return PIL.Image.open(io.BytesIO(image_data))


def get_image_from_path(path: str) -> Image:
    """
    Load an image from the specified file path.
    Args:
        path (str): The file path to load the image from.
    Returns:
        Image: The loaded PIL Image.
    """
    import PIL.Image
    # Open the image using PIL
    return PIL.Image.open(path)


def display_image_from_b64(image_b64: str) -> None:
    """
    Display a base64-encoded image.

    Args:
        image_b64 (str): The base64-encoded image string.
    """
    image = get_image_from_b64(image_b64=image_b64)
    image.show()
