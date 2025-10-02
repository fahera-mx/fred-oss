import PIL.Image

from fred.utils.imout.catalog import ImageOutputCatalog


def test_image_output_catalog_b64():
    image = PIL.Image.new("RGB", (100, 100))
    output_handler = ImageOutputCatalog.B64(image=image)
    output_b64 = output_handler.out()

    assert output_b64 is not None
    assert isinstance(output_b64, str)
    assert len(output_b64) > 0
