from fred.dao.comp._keyval import _get_minio_elements_from_key


def test__get_minio_elements_from_key():
    bucket, obj = _get_minio_elements_from_key("mybucket/myobject")
    assert bucket == "mybucket"
    assert obj == "myobject"

    bucket, obj = _get_minio_elements_from_key("/mybucket/myobject")
    assert bucket == "mybucket"
    assert obj == "myobject"

    bucket, obj = _get_minio_elements_from_key("mybucket/myobject/with/slashes")
    assert bucket == "mybucket"
    assert obj == "myobject/with/slashes"

    bucket, obj = _get_minio_elements_from_key("/mybucket/myobject/with/slashes")
    assert bucket == "mybucket"
    assert obj == "myobject/with/slashes"
