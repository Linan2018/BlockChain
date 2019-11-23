from BlockChain import BlockChain
from uuid import uuid4
import json
import time
import threading
import socket

# unique address for this node
node_identifier = str(uuid4()).replace('-', '')

blockchain = BlockChain()

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
s.close()

lock = threading.Lock()


def listen():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    s.bind(('', port))
    print('Listening for broadcast at ', s.getsockname())

    while True:
        data, address = s.recvfrom(65535)
        receive(data)


def broadcast(content):
    print('广播:', content['type'])
    s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    network = '<broadcast>'
    s_.sendto(json.dumps(content).encode('utf-8'), (network, port))
    s_.close()


def mine():
    global lock
    global blockchain

    while True:
        lock.acquire()

        if blockchain.mine_pending_transaction(node_identifier):
            # We run the proof of work algorithm to get the next proof...
            content = {
                'type': 'chain',
                'chain': blockchain.chain
            }

            broadcast(content)

        lock.release()


def register_nodes(node):
    global blockchain
    global lock

    lock.acquire()
    blockchain.register_node(node)
    print("register_nodes")

    content = {
        'type': 'node',
        'node': node_identifier,
        'ip': ip
    }

    broadcast(content)

    lock.release()

    return


def receive(data):
    global blockchain

    data = json.loads(data.decode('utf-8'))

    required = ['chain', 'transaction', 'node']
    if not any(k in data for k in required):
        print('收到无效信息')
        # print(data)
        return

    if data['type'] == 'chain':
        blockchain.replace_chain(data['chain'])
        print('Receive a new chain.')
        print('现在共有{}个区块'.format(len(blockchain.chain)))

    elif data['type'] == 'transaction':
        blockchain.add_transaction(data['transaction'])

    elif data['type'] == 'node':
        blockchain.register_node(data['ip'])
        print('Receive a new node.')
        print('现在共有{}个节点'.format(len(blockchain.nodes)))
    else:
        print('收到无效信息')
    return


def wait():
    global lock
    lock.acquire()
    print('loading')
    time.sleep(5)
    lock.release()


if __name__ == '__main__':
    t_listen = threading.Thread(target=listen)
    t_wait = threading.Thread(target=wait)
    t_reg = threading.Thread(target=register_nodes, args=(ip,))
    t_mine = threading.Thread(target=mine)

    t_listen.start()
    t_wait.start()
    t_reg.start()
    t_mine.start()
