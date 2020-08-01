from typing import Dict, List, Optional

from web3.exceptions import ExtraDataLengthError
from web3.middleware import geth_poa_middleware

from brownie.network.middlewares import BrownieMiddlewareBase


class GethPOAMiddleware(BrownieMiddlewareBase):
    def __init__(self, make_request, w3):
        self.w3 = w3
        self.make_request = make_request
        self.middleware_fn = geth_poa_middleware(make_request, w3)

    @classmethod
    def get_layer(cls, w3, network_config: Dict) -> Optional[int]:
        try:
            w3.eth.getBlock("latest")
            return None
        except ExtraDataLengthError:
            return 100

    def __call__(self, method: str, params: List) -> Dict:
        return self.middleware_fn(method, params)
