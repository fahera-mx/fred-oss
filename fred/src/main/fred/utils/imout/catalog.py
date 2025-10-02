import enum

from PIL.Image import Image

from fred.utils.imout.interface import ImageOutputInterface
from fred.utils.imout._filesystem import OutputFilesystem
from fred.utils.imout._string import OutputString


class ImageOutputCatalog(enum.Enum):
    B64 = OutputString
    STRING = OutputString
    FILESYSTEM = OutputFilesystem 

    def __call__(self, image: Image, **kwargs) -> ImageOutputInterface:
        if getattr(self.value, "auto", None):
            return self.value.auto(image=image, **kwargs)
        return self.value(image=image, **kwargs)
