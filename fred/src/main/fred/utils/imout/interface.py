from dataclasses import dataclass
from typing import Any, Optional

from PIL.Image import Image


class ImageOutputBackendInterface:
    metadata: dict = {}
    client: Optional[Any] = None  # Placeholder for clients like MinIO, S3, etc.


@dataclass(frozen=True, slots=True)
class ImageOutputInterface(ImageOutputBackendInterface):
    """Interface for image output handling."""
    image: Image

    @classmethod
    def auto(cls, **kwargs) -> 'ImageOutputInterface':
        return cls(**kwargs)

    @classmethod
    def from_path(cls, path: str) -> "ImageOutputInterface":
        from fred.utils.imops import get_image_from_path

        image = get_image_from_path(path=path)
        return cls(image=image)

    def save(self, path: str, format: str = "PNG"):
        """Save the image to a file."""
        self.image.save(path, format=format)

    def show(self):
        """Display the image."""
        self.image.show()

    def out(self, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement out method.")
