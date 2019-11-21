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

# 没写监听 广播加进去了 没写main 考虑用多进程

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = BlockChain()


# @app.route('/mine', methods=['GET'])
def mine():
    block = blockchain.mine_pending_transaction(node_identifier)
    # We run the proof of work algorithm to get the next proof...

    content = {
        'type': 'block',
        'block': block
    }

    udp.broadcast(content)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
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

    udp.broadcast(content)

    # Create a new Transaction
    blockchain.add_transaction(values)

    response = {'message': f'A transaction will be added to Block Chain'}

    # response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    node = values.get('node')
    if node is None:
        return "Error: Please supply a valid list of nodes", 400

    # 广播 ##########################
    content = {
        'type': 'node',
        'message': 'Add a new node: ' + '"{}"'.format(node),
        'node': node
    }

    udp.broadcast(content)
    # 广播结束 ##########################

    blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    """
    查询其他所有节点
    :return: resolve后的chain
    """
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

    required = ['sender', 'recipient', 'amount']
    if not any(k in data for k in required):
        print('收到无效信息')
        return

    if data['type'] == 'block':
        blockchain.chain.append(data['block'])
        print('Receive a new block.')
    elif data['type'] == 'transaction':
        blockchain.add_transaction(data['transaction'])
        print('Receive a new transaction.')
    elif data['type'] == 'node':
        blockchain.register_node(data['node'])
        print('Receive a new node.')
    else:
        print('收到无效信息')
    return


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

    locka = threading.Lock()
    lockb = threading.Lock()
    lockc = threading.Lock()

    ta = threading.Thread(target=app.run, args=('0.0.0.0', 5000))
    tb = threading.Thread(target=mine)
    tc = threading.Thread(target=udp.listen)

    locka.acquire()  # 保证a先执行

    ta.start()
    tb.start()
    tc.start()

    # ta.join()

    #
    # pid = os.fork()
    # if pid == 0:
    #     print('app进程: I am child process (%s) and my parent is %s.' % (os.getpid(), os.getppid()))
    # else:
    #     print('监听进程: I (%s) just created a child process (%s).' % (os.getpid(), pid))
    #     # app.run(host='0.0.0.0', port=5000)
