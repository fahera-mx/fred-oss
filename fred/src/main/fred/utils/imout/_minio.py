import posixpath

from fred.utils.imout.interface import ImageOutputInterface


class OutputMinio(ImageOutputInterface):
    """MinIO image output handling."""

    @classmethod
    def auto(cls, **kwargs) -> "OutputMinio":
        from fred.dao.service.catalog import ServiceCatalog
        from fred.dao.comp.catalog import CompCatalog

        minio = ServiceCatalog.MINIO.auto(**kwargs)
        if "minio_endpoint" in minio.metadata:
            cls.metadata["minio_endpoint"] = minio.metadata["minio_endpoint"]
        cls.client = CompCatalog.KEYVAL.mount(minio)
        return cls(**kwargs)

    def out(self, bucket: str, filename: str, presigned: bool = False, **kwargs) -> str:
        from fred.utils.imops import image_to_b64

        image_string = image_to_b64(self.image)
        self.client(key=filename).set(image_string, b64=True, bucket=bucket, **kwargs)
        if not presigned:
            return posixpath.join(
                self.metadata.get("minio_endpoint", ""),
                bucket,
                filename,
            )
        # TODO: Implement the generation of a pre-signed URL
        # https://github.com/minio/minio-py/blob/master/docs/API.md#get_presigned_url
        raise NotImplementedError("Presigned URL generation is not yet implemented.")
