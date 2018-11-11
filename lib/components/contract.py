#!/usr/bin/python3

from collections import OrderedDict
import sys

from lib.components.eth import web3, TransactionReceipt

class _ContractBase:

    def __init__(self, abi):
        self.abi = abi
        self.topics = dict((
            i['name'], 
            web3.toHex(web3.sha3(
                text=i['name']+",".join(x['type'] for x in i['inputs'])
                ))
        ) for i in abi if i['type']=="event")


class ContractDeployer(_ContractBase):

    def __init__(self, interface):
        self.bytecode = interface['bin']
        self._deployed = OrderedDict()
        super().__init__(interface['abi'])
    
    def deploy(self, account, *args):
        contract = web3.eth.contract(abi = self.abi, bytecode = self.bytecode)
        receipt = account._contract_call(contract.constructor, args, {})
        return self.at(receipt.contractAddress, account)
    
    def at(self, address, owner = None):
        address = web3.toChecksumAddress(address)
        if address in self._deployed:
            return self._deployed[address]
        self._deployed[address] = Contract(address, self.abi, owner)
        return self._deployed[address]
    
    def addresses(self):
        return list(self._deployed)

    def __iter__(self):
        return iter(self._deployed.values())

    def __getitem__(self, i):
        return list(self._deployed.values())[i]


class Contract(_ContractBase):

    def __init__(self, address, abi, owner):
        super().__init__(abi)
        self._contract = web3.eth.contract(address = address, abi = abi)
        self._fn_map = dict((
            i['name'],
            True if i['stateMutability'] in ['view','pure'] else False
            ) for i in abi if i['type']=="function")
        self.owner = owner
    
    def __repr__(self):
        return "<Contract object '{}'>".format(self.address)

    def __getattr__(self, name):
        if name not in self._fn_map:
            return getattr(self._contract, name)
        def _call(*args):
            result = getattr(self._contract.functions,name)(*args).call()
            if type(result) is not list:
                return web3.toHex(result) if type(result) is bytes else result
            return [(web3.toHex(i) if type(i) is bytes else i) for i in result]
        def _tx(*args):
            if args and type(args[-1]) is dict:
                args, tx = (args[:-1], args[-1])
                if 'from' not in tx:
                    tx['from'] = self.owner
                if 'value' in tx and type(tx['value']) is float:
                    tx['value'] = int(tx['value'])
            else:
                tx = {'from': self.owner}
            fn = getattr(self._contract.functions,name)
            return tx['from']._contract_call(fn, args, tx)
        return _call if self._fn_map[name] else _tx

    def revert(self, name, *args):
        if name not in self._fn_map:
            raise AttributeError("{} is not a valid function.".format(name))
        try:
            self.__getattr__(name)(*args)
            return False
        except ValueError:
            return True

    def balance(self):
        return web3.eth.getBalance(self._contract.address)