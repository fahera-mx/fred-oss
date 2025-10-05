from urllib3 import PoolManager, Retry
from urllib3.util import Timeout

from fred.settings import get_environ_variable, logger_manager
from fred.dao.service.interface import ServiceConnectionPoolInterface

logger = logger_manager.get_logger(name=__name__)


class MinioConnectionPool(ServiceConnectionPoolInterface[PoolManager]):

    @classmethod
    def _create_pool(cls, disable_cert: bool = False, **kwargs) -> PoolManager:
        """Create a urllib3 PoolManager with the given configurations.

        TODO: Consider using the inverse of 'require_cert' as the default to ensure we do have cert-check automatically.
        For now, we keep it as is to avoid breaking changes.

        Args:
            require_cert (bool): Whether to require SSL certificate verification.
            **kwargs: Additional keyword arguments to pass to the PoolManager constructor.
        Returns:
            PoolManager: A configured PoolManager instance.
        """
        num_pools = kwargs.pop("num_pools", 10)
        maxsize = kwargs.pop("maxsize", 10)
        # Default timeout of 5 minutes
        timeout_seconds = kwargs.pop("timeout", 300)
        timeout = Timeout(
            connect=timeout_seconds,
            read=timeout_seconds,
        )
        # Default retries of 5 with exponential backoff
        retry = Retry(
            total=kwargs.pop("retries", 5),
            backoff_factor=kwargs.pop("backoff_factor", 0.25),
            status_forcelist=[500, 502, 503, 504],
        )
        # Configure certificate requirements for SSL connections
        cert_reqs = "CERT_NONE"
        ca_certs = None
        if not disable_cert:
            import certifi
            cert_reqs = "CERT_REQUIRED"
            ca_certs = get_environ_variable("SSL_CERT_FILE") or certifi.where()
        # Finally, create and return the PoolManager instance
        return PoolManager(
            num_pools=num_pools,
            maxsize=maxsize,
            timeout=timeout,
            retries=retry,
            cert_reqs=cert_reqs,
            ca_certs=ca_certs,
            **kwargs
        )
