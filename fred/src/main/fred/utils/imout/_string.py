from fred.utils.imout.interface import ImageOutputInterface


class OutputString(ImageOutputInterface):
    """String output handler for images."""

    def out(self) -> str:
        from fred.utils.imops import image_to_b64

        return image_to_b64(self.image)
