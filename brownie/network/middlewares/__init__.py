import importlib
from typing import Dict, List, Optional
from pathlib import Path


class BrownieMiddlewareBase:
    def __init__(self, make_request, w3):
        self.w3 = w3
        self.make_request = make_request

    @classmethod
    def get_layer(cls, w3, network_config: Dict) -> Optional[int]:
        """
        Return the target layer of this middleware.

        All builtin middlewares are considered to be on layer 0. Middlewares are called in
        ascending order prior to the request, and descending order after the request.
        """
        raise NotImplementedError

    def __call__(self, method: str, params: List) -> Dict:
        raise NotImplementedError


def add_middlewares(w3, network_config):
    middleware_layers = {}
    for obj in _middlewares:
        layer = obj.get_layer(w3, network_config)
        if layer is not None:
            middleware_layers.setdefault(layer, []).append(obj)

    for layer, obj in [(k, x) for k in sorted(middleware_layers) for x in middleware_layers[k]]:
        if layer < 0:
            w3.middleware_onion.inject(obj, layer=0)
        else:
            w3.middleware_onion.add(obj)


_middlewares = []

for path in Path(__file__).parent.glob("[!_]*.py"):
    # load middleware classes from all modules within `brownie/networks/middlewares/`
    # to be included the module name must not begin with `_` and the middleware
    # must subclass `BrownieMiddlewareBase`
    module = importlib.import_module(f"{__package__}.{path.stem}")
    _middlewares.extend(
        obj
        for obj in module.__dict__.values()
        if isinstance(obj, type)
        and obj.__module__ == module.__name__
        and BrownieMiddlewareBase in obj.mro()
    )
