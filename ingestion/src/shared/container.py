from typing import Dict, Type, Any, Callable
import logging
from .interfaces import ConfigProvider, Logger


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


class DefaultLogger:
    """Default logger implementation"""

    def __init__(self, config: ConfigProvider):
        self._logger = logging.getLogger(__name__)
        logging.basicConfig(level=getattr(logging, config.log_level.upper()))

    def info(self, message: str, *args, **kwargs) -> None:
        self._logger.info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        self._logger.error(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        self._logger.debug(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        self._logger.warning(message, *args, **kwargs)


def create_container() -> DIContainer:
    """Create and configure the DI container"""
    container = DIContainer()

    # Register config
    from .utils import Config

    config = Config()
    container.register_singleton(ConfigProvider, config)

    # Register logger
    logger = DefaultLogger(config)
    container.register_singleton(Logger, logger)

    return container
