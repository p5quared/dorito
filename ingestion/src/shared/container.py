from typing import Dict, Type, Any, Callable
from .interfaces import ConfigProvider


class DIContainer:
    """Simple dependency injection container"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}

    def register_singleton(self, interface: Type, implementation: Any) -> None:
        """Register a singleton service"""
        self._singletons[interface] = implementation

    def register_factory(self, interface: Type, factory: Callable[[], Any]) -> None:
        """Register a factory function for a service"""
        self._factories[interface] = factory

    def register(self, interface: Type, implementation: Any) -> None:
        """Register a service implementation"""
        self._services[interface] = implementation

    def get(self, interface: Type) -> Any:
        """Get a service instance"""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check factories
        if interface in self._factories:
            return self._factories[interface]()

        # Check regular services
        if interface in self._services:
            return self._services[interface]

        raise ValueError(f"Service not registered: {interface}")




def create_container() -> DIContainer:
    """Create and configure the DI container"""
    container = DIContainer()

    # Register config
    from .utils import Config

    config = Config()
    container.register_singleton(ConfigProvider, config)

    return container
