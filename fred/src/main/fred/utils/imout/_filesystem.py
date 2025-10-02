from fred.utils.imout.interface import ImageOutputInterface


class OutputFilesystem(ImageOutputInterface):
    """Filesystem output handler for images."""

    def out(self, path: str) -> str:
        from fred.utils.imops import save_image_to_path

        save_image_to_path(image=self.image, path=path)
        return path