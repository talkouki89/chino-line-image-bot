# -- coding utf-8 --

from ..helper import ChrHelperProtocol
from .BaseService import BaseServiceSender


class ShopAuthService(ChrHelperProtocol):
    __REQ_TYPE = 4
    __RES_TYPE = 4
    __ENDPOINT = "/SHOPA"

    def __init__(self):
        self.__sender = BaseServiceSender(
            self.client,
            __class__.__name__,
            self.__REQ_TYPE,
            self.__RES_TYPE,
            self.__ENDPOINT,
        )

    def establishE2EESession(self, clientPublicKey: str):
        METHOD_NAME = "establishE2EESession"
        METHOD_NAME = "establishE2EESession"
        params = [[12, 1, [[11, 1, clientPublicKey]]]]
        return self.__sender.send(METHOD_NAME, params)
        return self.__sender.send(METHOD_NAME, params)
