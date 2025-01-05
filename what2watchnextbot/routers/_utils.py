import typing
from collections.abc import Callable, Iterable

import aiogram
from aiogram.dispatcher.event.telegram import CallbackType, TelegramEventObserver


def _router_update_observers(router: aiogram.Router) -> Iterable[TelegramEventObserver]:
    for name, observer in router.observers.items():
        if name not in ["update", "error"]:
            yield observer


def handler_for_all_updates(
    router: aiogram.Router,
    *filters: CallbackType,
    flags: dict[str, typing.Any] | None = None,
    **kwargs: typing.Any,
):
    def decorator[T, **P](wrapped: Callable[P, T]) -> Callable[P, T]:
        if isinstance(router, aiogram.Dispatcher):
            router.update.register(wrapped, *filters, flags=flags, **kwargs)
        else:
            for observer in _router_update_observers(router):
                observer.register(wrapped, *filters, flags=flags, **kwargs)

        return wrapped

    return decorator


def middleware_for_all_updates(router: aiogram.Router):
    def decorator[T, **P](wrapped: Callable[P, T]) -> Callable[P, T]:
        if isinstance(router, aiogram.Dispatcher):
            router.update.middleware.register(wrapped)
        else:
            for observer in _router_update_observers(router):
                observer.middleware.register(wrapped)

        return wrapped

    return decorator


def outer_middleware_for_all_updates(router: aiogram.Router):
    def decorator[T, **P](wrapped: Callable[P, T]) -> Callable[P, T]:
        if isinstance(router, aiogram.Dispatcher):
            router.update.outer_middleware.register(wrapped)
        else:
            for observer in _router_update_observers(router):
                observer.outer_middleware.register(wrapped)

        return wrapped

    return decorator
