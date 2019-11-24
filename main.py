#!/bin/python3
# coding=utf-8
import json
import socket
import threading
from uuid import uuid4

from BlockChain import BlockChain

# unique address for this node
node_identifier = str(uuid4()).replace('-', '')

blockchain = BlockChain()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
s.close()


def listen():
    s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    s_.bind(('', port))
    print('Thread2: Listening for broadcast at ', s_.getsockname())

    while True:
        data, address = s_.recvfrom(65535)
        receive(data, address[0])


def broadcast(content):
    print('Thread1: broadcast ', content['type'])
    s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    network = '<broadcast>'
    s_.sendto(json.dumps(content).encode('utf-8'), (network, port))
    s_.close()


def mine():
    global blockchain

    register_nodes(ip)

    while True:

        if blockchain.mine_pending_transaction(ip):
            # We run the proof of work algorithm to get the next proof...
            content = {
                'type': 'chain',
                'chain': blockchain.chain,
                'node': node_identifier
            }

            broadcast(content)


def register_nodes(node):
    global blockchain

    blockchain.register_node(node)

    content = {
        'type': 'node',
        'node': node_identifier,
        'ip': ip
    }

    broadcast(content)


def receive(data, address):
    global blockchain

    data = json.loads(data.decode('utf-8'))

    required = ['chain', 'transaction', 'node']
    if not any(k in data for k in required):
        print('Thread2: Receive an invalid msg!')
        # print(data)
        return

    if data['type'] == 'chain':
        if data['node'] != node_identifier:
            print('Thread2: Receive a new chain with a length of {}'.format(len(data['chain'])))
            print('Thread2: The length of our chain is {}'.format(len(blockchain.chain)))
            blockchain.replace_chain(data['chain'], address)

    elif data['type'] == 'transaction':
        blockchain.add_transaction(data['transaction'])

    elif data['type'] == 'node':
        blockchain.register_node(address)
        print('Thread2: Receive a new node...')

    else:
        print('Thread2: Receive an invalid msg!')
    return


if __name__ == '__main__':
    t_listen = threading.Thread(target=listen)
    t_mine = threading.Thread(target=mine)

    t_listen.start()
    t_mine.start()
