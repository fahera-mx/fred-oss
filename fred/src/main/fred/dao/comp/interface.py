from typing import Optional
from fred.dao.service.interface import ServiceInterface
from fred.dao.service.catalog import ServiceCatalog

SRV_REF_TYPE = str | ServiceInterface | ServiceCatalog


class SrvCompanionMixin:
    _srv: ServiceInterface
    _cat: ServiceCatalog

    @classmethod
    def _set_srv(cls, srv_ref: Optional[SRV_REF_TYPE] = None, **kwargs):
        """Sets the service instance for the component class.
        This method initializes the `_srv` class variable with an instance
        of the service specified by `name` and any additional parameters passed via `kwargs`.
        Args:
            name (Optional[str]): The name of the service to set. Defaults to "REDIS".
            **kwargs: Additional keyword arguments to configure the service instance.
        """
        match (srv_ref or "REDIS"):
            case str() as name:
                cls._cat = ServiceCatalog[name.upper()]
                cls._srv = cls._cat.auto(**kwargs)
            case ServiceCatalog() as cat:
                cls._cat = cat
                cls._srv = cat.auto(**kwargs)
            case ServiceInterface() as instance:
                cls._srv = instance
                cls._cat = ServiceCatalog.from_classname(
                    classname=instance.__class__.__name__
                )
            case _:
                raise ValueError(f"Invalid service '{srv_ref}' type: {type(srv_ref)}")
    
    @property
    def _nme(self) -> str:
        """Returns the class name of the current service instance."""
        return self._srv.__class__.__name__


class ComponentInterface(SrvCompanionMixin):

    @classmethod
    def mount(cls, srv_ref: Optional[SRV_REF_TYPE] = None, **kwargs) -> type["ComponentInterface"]:
        """Mounts the component to a specific service instance.
        This method configures the component to use a service instance
        identified by `srv_name` and any additional parameters passed via `kwargs`.
        
        Args:
            srv_name (Optional[str]): The name of the service to mount. Defaults to "REDIS".
            **kwargs: Additional keyword arguments to configure the service instance.
        """
        cls._set_srv(srv_ref=srv_ref, **kwargs)
        return cls

    @classmethod
    def auto(cls, srv_ref: Optional[SRV_REF_TYPE] = None, **kwargs) -> "ComponentInterface":
        """Automatically creates an instance of the component, mounting it to a service.
        This method is a convenience wrapper that first mounts the component to a service
        and then creates an instance of the component.
        Args:
            srv_name (Optional[str]): The name of the service to mount. Defaults to "REDIS".
            **kwargs: Additional keyword arguments for both mounting the service and
                      creating the component instance. If there are specific arguments
                      for the service, they should be passed under the key `srv_kwargs`
                      as a dictionary.
        """
        srv_kwargs = kwargs.pop("srv_kwargs", {})
        return cls.mount(srv_ref=srv_ref, **srv_kwargs)(**kwargs)
