# BlockChain
基于局域网广播的去中心化区块链系统

## Note
- 使用python3.6
- 打开4000端口

## Setup

```
firewall-cmd --zone=public --add-port=4000/udp --permanent
firewall-cmd --reload
```

```
git init
https://github.com/Linan2018/BlockChain.git
cd BlockChain
python3 main.py
```
