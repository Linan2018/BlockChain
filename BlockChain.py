import time
import hashlib
import json
import requests
from flask import request
from urllib.parse import urlparse


class BlockChain:
    def __init__(self):

        # 节点列表
        self.nodes = set()

        # 初始化链，添加创世区块
        self.chain = [self.__create_genesis_block()]

        # 设置初始难度
        self.difficulty = 4

        # 设置一个挖矿奖励
        self.mining_reward = 5

        # 待处理交易
        self.__pending_transactions = []

    @staticmethod
    def calculate_hash(block):
        """
        计算区块的哈希值
        :return: 哈希值
        """
        # 将区块信息拼接然后生成sha256的hash值
        raw_str = block['previous_hash'] + \
                  str(block['index']) + \
                  str(block['timestamp']) + \
                  json.dumps(block['transactions'], ensure_ascii=False) + \
                  str(block['proof'])

        sha256 = hashlib.sha256()
        sha256.update(raw_str.encode('utf-8'))
        hash_ = sha256.hexdigest()
        return hash_

    # @staticmethod
    def __create_genesis_block(self):
        """
        生成创世区块
        :return: 创世区块
        """
        block = {
            'index': 0,
            'previous_hash': "",
            'timestamp': time.clock(),
            'transactions': [],
            'proof': 0,
            'hash': ''
        }
        block["hash"] = self.calculate_hash(block)
        return block

    @property
    def latest_block(self):
        """
        获取链上最后一个也是最新的一个区块
        :return:最后一个区块
        """
        return self.chain[-1]

    def add_transaction(self, sender, recipient, amount):
        """
        添加交易
        """
        # 这里应该根据业务对交易进行一些列的验证
        '''TODO'''
        # 添加到待处理交易
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }
        self.__pending_transactions.append(transaction)

    def verify_blockchain(self, chain):
        """
        校验特定区块链数据是否完整 是否被篡改过
        :param chain: <list> A blockchain
        :return: <bool> 校验结果
        """

        if len(chain) == 1:
            return True

        for i in range(1, len(chain)):
            current_block = chain[i]  # 当前遍历到的区块
            previous_block = chain[i - 1]  # 当前区块的上一个区块

            # 检验pow是否正确
            if current_block["hash"] != self.calculate_hash(current_block):
                # 如果当前区块的hash值不等于计算出的hash值，说明数据有变动
                return False
            if current_block["previous_hash"] != self.calculate_hash(previous_block):
                # 如果当前区块记录的上个区块的hash值不等于计算出的上个区块的hash值 说明上个区块数据有变动或者本区块记录的上个区块的hash值被改动
                return False
        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                print(node, length, max_length, self.verify_blockchain(chain))

                # Check if the length is longer and the chain is valid
                if length > max_length and self.verify_blockchain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def mine_block(self, block):
        """
        """
        time_start = time.clock()

        # 要求hash值前difficulty个位为0
        while block['hash'][0: self.difficulty] != '0' * self.difficulty:
            if block['index'] == len(self.chain):
                # 符合要求
                block['proof'] += 1
                block['hash'] = self.calculate_hash(block)
            else:
                return False

        print("挖到区块:%s, 耗时: %f秒" % (block['hash'], time.clock() - time_start))
        return True

    def mine_pending_transaction(self, mining_reward_address):
        """
        挖取待处理交易
        :param mining_reward_address: 挖矿奖励的地址
        :return:
        """
        block = {
            'index': len(self.chain),
            'previous_hash': self.latest_block["hash"],
            'timestamp': time.time(),
            'transactions': self.__pending_transactions,
            'proof': 0,
            'hash': ''
        }
        block['hash'] = self.calculate_hash(block)

        # self.mine_block(self.difficulty)
        if self.mine_block(block):
            self.chain.append(block)
            # 挖矿成功后 重置待处理事务 添加一笔事务 就是此次挖矿的奖励
            self.__pending_transactions = [{
                'sender': "",
                'recipient': mining_reward_address,
                'amount': self.mining_reward,
            }]
            print(mining_reward_address, "挖矿成功，添加一笔事务，作为此次挖矿的奖励")
            return True, block
        else:
            print(mining_reward_address, "挖矿失败，其他节点已经成功挖矿")
            return False, None

    def get_balance_of_address(self, address):
        """
        获取钱余额
        :param address: 钱包地址
        :return: 余额
        """
        balance = 0
        for block in self.chain:
            for trans in block["transactions"]:
                if trans["sender"] == address:
                    # 自己发起的交易 支出
                    balance -= trans["amount"]
                if trans["recipient"] == address:
                    # 收入
                    balance += trans["amount"]
        return balance

    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        print(parsed_url)
        self.nodes.add(parsed_url.netloc)


if __name__ == '__main__':
    # 测试使用区块链
    blockChain = BlockChain()
    # print(dir(blockChain))
    # 添加两笔交易
    blockChain.add_transaction("address1", "address2", 100)
    blockChain.add_transaction("address2", "address1", 50)
    # address3 挖取待处理的交易
    # for b in blockChain.chain:
    #     print(b["transactions"])
    # 查看账户余额
    blockChain.mine_pending_transaction('address3')
    # for b in blockChain.chain:
    #     print(b["transactions"])
    # 查看账户余额
    print('address1 余额 ', blockChain.get_balance_of_address('address1'))
    print('address2 余额 ', blockChain.get_balance_of_address('address2'))
    print('address3 余额 ', blockChain.get_balance_of_address('address3'))
    # address2 挖取待处理的交易
    blockChain.mine_pending_transaction('address2')
    # for b in blockChain.chain:
    #     print(b["transactions"])
    print('address1 余额 ', blockChain.get_balance_of_address('address1'))
    print('address2 余额 ', blockChain.get_balance_of_address('address2'))
    print('address3 余额 ', blockChain.get_balance_of_address('address3'))
    blockChain.mine_pending_transaction('address3')
    blockChain.mine_pending_transaction('address3')
    blockChain.mine_pending_transaction('address3')
    print('address1 余额 ', blockChain.get_balance_of_address('address1'))
    print('address2 余额 ', blockChain.get_balance_of_address('address2'))
    print('address3 余额 ', blockChain.get_balance_of_address('address3'))