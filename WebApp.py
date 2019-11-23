import json
import os
from uuid import uuid4

from flask import Flask
from flask import jsonify
from flask import request
from multiprocessing import Pool
import os, time, random
import udp
from BlockChain import BlockChain
import threading
import socket

lock = threading.Lock()
lock2 = threading.Lock()
# 没写监听 广播加进去了 没写main 考虑用多进程

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = BlockChain()

# global ip
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
s.close()


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
    print('广播', content['type'])
    # print("广播内容")
    # try:
    #     print(content['block']['hash'])
    # except:
    #     pass
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    port = 4000

    network = '<broadcast>'
    s.sendto(json.dumps(content).encode('utf-8'), (network, port))
    s.close()


# @app.route('/mine', methods=['GET'])

def mine():
    global lock
    # global lock2
    global blockchain

    while True:
        lock.acquire()
        # lock2.release()
        # print(blockchain.resolve_conflicts())
        # print("mine!!", id(blockchain))
        if blockchain.mine_pending_transaction(node_identifier):
            # We run the proof of work algorithm to get the next proof...
            content = {
                'type': 'chain',
                'chain': blockchain.chain
            }

            broadcast(content)
        lock.release()

    # response = {
    #     'message': "New Block Forged",
    #     'index': block['index'],
    #     'transactions': block['transactions'],
    #     'proof': block['proof'],
    #     'previous_hash': block['previous_hash'],
    # }
    # return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    global blockchain
    # global lock2

    # lock2.acquire()
    print("chain!!", id(blockchain))
    print("进入get")
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    global blockchain
    values = request.get_json()
    # print(values)

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    content = {
        'type': 'transaction',
        'message': 'Add a new transaction.',
        'transaction': values
    }

    broadcast(content)

    # Create a new Transaction
    blockchain.add_transaction(values)

    response = {'message': 'A transaction will be added to Block Chain'}

    # response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


def register_nodes(node):
    global blockchain

    global lock
    lock.acquire()
    blockchain.register_node(node)
    # values = request.get_json()
    #
    # node = values.get('node')
    # if node is None:
    #     return "Error: Please supply a valid list of nodes", 400
    print("register_nodes")
    # 广播 ##########################
    content = {
        'type': 'node',
        'node': node_identifier,
        'ip': ip
    }


    broadcast(content)

    lock.release()
    # 广播结束 ##########################

    return


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """
    查询其他所有节点
    :return: resolve后的chain
    """
    global blockchain
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


def receive(data):
    data = json.loads(data.decode('utf-8'))

    required = ['chain', 'transaction', 'node']
    if not any(k in data for k in required):
        print('收到无效信息')
        # print(data)
        return

    if data['type'] == 'chain':
        blockchain.replace_chain(data['chain'])
        print('现在共有{}个区块'.format(len(blockchain.chain)))

        # blockchain.chain.append(data['block'])
        # print('Receive a new block.')
        # print('收到消息hash：', data['block']['hash'])
    elif data['type'] == 'transaction':
        blockchain.add_transaction(data['transaction'])
        print('Receive a new transaction.')
        # print('现在共有{}比交易'.format(len(blockchain.chain)))
    elif data['type'] == 'node':
        blockchain.register_node(data['ip'])
        print(data)
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
    # print('Parent process {}.'.format(os.getpid()))
    # p = Pool()
    #
    # p.apply(app.run, args=('0.0.0.0', 5000))
    # p.apply(udp.listen)
    #
    # # for i in range(5):
    # #     p.apply_async(long_time_task, args=(i,))
    # print('Waiting for all subprocesses done...')
    # p.close()
    # p.join()
    # print('All subprocesses done.')



    tc = threading.Thread(target=listen)
    ta = threading.Thread(target=app.run, args=('0.0.0.0', 5000))

    t_wait = threading.Thread(target=wait)

    t = threading.Thread(target=register_nodes, args=(ip,))
    tb = threading.Thread(target=mine)
    # lock_register.acquire()  # 保证a先执行

    tc.start()
    # ta.start()
    t_wait.start()
    t.start()
    tb.start()

    # t.join()

    #
    # pid = os.fork()
    # if pid == 0:
    #     print('app进程: I am child process (%s) and my parent is %s.' % (os.getpid(), os.getppid()))
    # else:
    #     print('监听进程: I (%s) just created a child process (%s).' % (os.getpid(), pid))
    #     # app.run(host='0.0.0.0', port=5000)
