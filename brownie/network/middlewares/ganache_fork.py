from typing import Callable, Dict, List, Optional

from brownie.network.middlewares import BrownieMiddlewareBase


class GanacheForkMiddleware(BrownieMiddlewareBase):

    """
    Web3 middleware for raising more expressive exceptions when a forked local network
    cannot access archival states.
    """

    def __init__(self, make_request: Callable, w3):
        self.w3 = w3
        self.make_request = make_request

    @classmethod
    def get_layer(cls, w3, network_config) -> Optional[int]:
        if "fork" in network_config:
            return 90
        return None

    def __call__(self, method: str, params: List) -> Dict:
        response = self.make_request(method, params)
        err_msg = response.get("error", {}).get("message", "")
        if (
            err_msg == "Returned error: project ID does not have access to archive state"
            or err_msg.startswith("Returned error: missing trie node")
        ):
            raise ValueError(
                "Local fork was created more than 128 blocks ago and you do not"
                " have access to archival states. Please restart your session."
            )

        return response
