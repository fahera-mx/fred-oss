import PIL.Image

from fred.utils.imops import (
    image_to_b64,
    get_image_from_b64,
)


def test_image_to_b64():

    image = PIL.Image.new("RGB", (100, 100))
    image_b64 = image_to_b64(image=image)

    assert image_b64 is not None
    assert isinstance(image_b64, str)


def test_get_image_from_b64():
    image = PIL.Image.new("RGB", (100, 100))
    image_b64 = image_to_b64(image=image)
    image_restored = get_image_from_b64(image_b64=image_b64)

    assert image_restored is not None
    assert isinstance(image_restored, PIL.Image.Image)
    assert image_restored.size == (100, 100)
    assert image_restored.mode == "RGB"
