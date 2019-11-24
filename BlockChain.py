# coding=utf-8
import hashlib
import json
import random
import sys
import time


class BlockChain:
    def __init__(self):

        # 节点列表
        self.nodes = set()

        # 初始化链，添加创世区块
        self.chain = [self.__create_genesis_block()]

        # 设置初始难度
        self.difficulty = 5

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

    def __create_genesis_block(self):
        """
        生成创世区块
        :return: 创世区块
        """
        block = {
            'index': 0,
            'previous_hash': "",
            'timestamp': 0,
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

    def add_transaction(self, transaction):
        """
        添加交易
        """
        # 这里应该根据业务对交易进行一些验证
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

    def mine_block(self, mining_reward_address):
        """
        """

        success = True

        block = {
            'index': len(self.chain),
            'previous_hash': self.latest_block["hash"],
            'timestamp': time.time(),
            'transactions': self.__pending_transactions,
            'proof': random.randint(0, sys.maxsize),
            'hash': ''
        }
        block['hash'] = self.calculate_hash(block)

        print('Thread1: Mining...')
        time_start = time.clock()

        # 要求hash值前difficulty位为0
        while block['hash'][0: self.difficulty] != '0' * self.difficulty:
            if block['index'] == len(self.chain):
                block['proof'] += 1
                block['hash'] = self.calculate_hash(block)
            else:
                success = False
                break

        if success:
            print("Thread1: Find a new block:%s, take %fs" % (block['hash'], time.clock() - time_start))
            self.chain.append(block)
            print('Thread1: The length of our chain is {}'.format(len(self.chain)))
            self.__pending_transactions = [{
                'sender': "",
                'recipient': mining_reward_address,
                'amount': self.mining_reward,
            }]
        else:
            print('Thread1: Mining failed.')
        return success

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

    def register_node(self, node):
        self.nodes.add(node)
        print('Now there is {} node(s).'.format(len(self.nodes)))

    def replace_chain(self, chain, mining_reward_address):
        if len(chain) > len(self.chain) and self.verify_blockchain(chain):
            self.chain = chain
            self.__pending_transactions = [{
                'sender': "",
                'recipient': mining_reward_address,
                'amount': self.mining_reward,
            }]
            print('Thread2: Replaced by the new chain!')
            print('Thread2: Now the length of our chain is {}.'.format(len(self.chain)))
