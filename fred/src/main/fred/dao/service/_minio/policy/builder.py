import enum


class MinioPolicyBuilderActionBucket(enum.StrEnum):
    ALL = "s3:*"
    LIST = "s3:ListBucket"
    LOCATION = "s3:GetBucketLocation"
    DELETE = "s3:DeleteBucket"
    CREATE = "s3:CreateBucket"


class MinioPolicyBuilderActionObject(enum.StrEnum):
    GET = "s3:GetObject"
    PUT = "s3:PutObject"
    DELETE = "s3:DeleteObject"
    ALL = "s3:*"
