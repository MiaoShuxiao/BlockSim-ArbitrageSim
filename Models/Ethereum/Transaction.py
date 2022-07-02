from Models.Ethereum.Distribution.DistFit import DistFit
import random
from InputsConfig import InputsConfig as p
import numpy as np
from Models.Network import Network
import operator
from Models.Ethereum.Distribution.DistFit import DistFit
import math
from queue import PriorityQueue
import copy

class Transaction(object):

    """ Defines the Ethereum Block model.

    :param int id: the uinque id or the hash of the transaction
    :param int timestamp: the time when the transaction is created. In case of Full technique, this will be array of two value (transaction creation time and receiving time)
    :param int sender: the id of the node that created and sent the transaction
    :param int to: the id of the recipint node
    :param int value: the amount of cryptocurrencies to be sent to the recipint node
    :param int size: the transaction size in MB
    :param int gasLimit: the maximum amount of gas units the transaction can use. It is specified by the submitter of the transaction
    :param int usedGas: the amount of gas used by the transaction after its execution on the EVM
    :param int gasPrice: the amount of cryptocurrencies (in Gwei) the submitter of the transaction is willing to pay per gas unit
    :param float fee: the fee of the transaction (usedGas * gasPrice)
    """

    def __init__(self,
	 id=0,
	 timestamp=0 or [],
	 sender=0,
     to=0,
     value=0,
     size=0.000546,
     gasLimit= 8000000,
     usedGas=0,
     gasPrice=0,
     fee=0,
     receiveTime=0,
     pickUpTime=0,
     executionTime=0,
     profit=0):

        self.id = id
        self.timestamp = timestamp
        self.sender = sender
        self.to= to
        self.value=value
        self.size = size
        self.gasLimit=gasLimit
        self.usedGas = usedGas
        self.gasPrice=gasPrice
        self.fee= usedGas * gasPrice
        self.receiveTime = receiveTime
        self.pickUpTime = pickUpTime
        self.executionTime = executionTime
        self.profit = profit


class LightTransaction():

    pool=[] # shared pool of pending transactions
    #x=0 # counter to only fit distributions once during the simulation

    def create_transactions(pickUpTime, prevTime):

        LightTransaction.pool=[]
        mean = math.ceil(pickUpTime - prevTime)


        if pickUpTime == 0 and prevTime == 0:
            mean = random.randint(0, p.Binterval) * p.Tn
        # little trick to generate genesis transactions
        if mean == 0:
            mean = 1
        Psize= round(random.expovariate(1 / mean))
        print(prevTime, pickUpTime, Psize)
        #if LightTransaction.x<1:
        #DistFit.fit() # fit distributions
        #gasLimit,usedGas,gasPrice,_ = DistFit.sample_transactions(Psize) # sampling gas based attributes for transactions from specific distribution

        for i in range(Psize):
            # assign values for transactions' attributes. You can ignore some attributes if not of an interest, and the default values will then be used
            tx= Transaction()

            tx.id= random.randrange(100000000000)
            senderInfo = random.choice (p.USERS)
            tx.sender = senderInfo.id
            tx.to= senderInfo.connectedMiner
            tx.size= random.expovariate(1/p.Tsize)
            tx.pickUpTime = pickUpTime
            tx.receiveTime = random.uniform(prevTime, pickUpTime)
            tx.gasLimit=21000
            tx.usedGas= random.expovariate(1/3000)
            tx.gasPrice = random.expovariate(1/4)
            tx.profit = 10 * (10 ** 18) #ETH

            participants = []
            for j in p.COALITIONS:
                prob = random.random()
                if(prob < j.probRate and j.users != []):
                    participants += [j]

            if len(participants) > 1:
                LightTransaction.create_auction(participants, tx, prevTime, pickUpTime)

            tx.fee= tx.usedGas * tx.gasPrice
            LightTransaction.pool += [tx]

        random.shuffle(LightTransaction.pool)


    ##### Select and execute a number of transactions to be added in the next block #####
    def execute_transactions(miner, currentTime):
        transactions= [] # prepare a list of transactions to be included in the block
        limit = 0 # calculate the total block gaslimit
        count = 0
        blocklimit = p.Blimit

        pool = sorted(LightTransaction.pool, key=lambda x: x.gasPrice, reverse=True) # sort pending transactions in the pool based on the gasPrice value

        while count < len(pool):
                if  (blocklimit >= pool[count].gasLimit):
                    blocklimit -= pool[count].usedGas
                    pool[count].miner=miner
                    pool[count].executionTime=currentTime
                    transactions += [pool[count]]
                    limit += pool[count].usedGas
                count+=1
        return transactions, limit


    def create_auction(participants, tx, prevTime, pickUpTime):
        auction = PriorityQueue()
        currTime = tx.receiveTime
        coalitionDict = {}
        for c1 in participants:
            #min_max
            selectedUser = -1
            minLatency = -99999
            selectedLatency = []
            for u in c1.users:
                latency = p.MATRIX[p.USERS[u].connectedMiner, :]
                calculateLatency = p.USERLATENCY
                for receiver in p.USERS:
                    calculateLatency[receiver.id] += latency[receiver.connectedMiner]
                calculateLatency[c1.users] = 0
                delay_time = min(calculateLatency[calculateLatency > 0])
                if minLatency < delay_time:
                    selectedUser = u
                    minLatency = delay_time
                    selectedLatency = calculateLatency
            coalitionDict[c1.id] = (selectedUser, selectedLatency)
        prevCoalition = next((e for e in p.COALITIONS if 1 in e.users), None)

        auctionResult = LightTransaction.exe_auction(participants, tx, prevCoalition, pickUpTime, coalitionDict)
        print(auctionResult)


    def exe_auction(participants, tx, prevCoalition, pickUpTime, coalitionDict):
        bids = PriorityQueue()
        latestTxFromCoalition = {}
        latestTxFromCoalition[prevCoalition] = tx
        bids.put((tx.receiveTime, tx))
        currentTime = tx.receiveTime
        while currentTime < pickUpTime:
            currBid = bids.get()[1]
            currentTime = currBid.receiveTime
            for c in participants:
                if currBid.sender in c.users:
                    continue
                listener = coalitionDict[prevCoalition.id][1]
                listenDelay = min(listener[c.users])
                if (c.id not in latestTxFromCoalition) or (latestTxFromCoalition[c.id].gasPrice < currBid.gasPrice):
                    newBid = copy.deepcopy(currBid)
                    newBid.gasPrice = newBid.gasPrice * 1.20
                    newBid.sender = coalitionDict[c.id][0]
                    newBid.to = p.USERS[u].connectedMiner
                    newBid.receiveTime = newBid.receiveTime + listenDelay + p.USERLATENCY[u]
                    latestTxFromCoalition[c.id] = newBid
                    bids.put((newBid.receiveTime, newBid))
        return latestTxFromCoalition


class FullTransaction():
    x=0 # counter to only fit distributions once during the simulation

    def create_transactions():
        Psize= int(p.Tn * p.Binterval)

        if FullTransaction.x<1:
            DistFit.fit() # fit distributions
        gasLimit,usedGas,gasPrice,_ = DistFit.sample_transactions(Psize) # sampling gas based attributes for transactions from specific distribution

        for i in range(Psize):
            # assign values for transactions' attributes. You can ignore some attributes if not of an interest, and the default values will then be used
            tx= Transaction()

            tx.id= random.randrange(100000000000)
            creation_time= random.randint(0,p.simTime-1)
            receive_time= creation_time
            tx.timestamp= [creation_time,receive_time]
            sender= random.choice (p.NODES)
            tx.sender = sender.id
            tx.to= random.choice (p.NODES).id
            tx.gasLimit=gasLimit[i]
            tx.usedGas=usedGas[i]
            tx.gasPrice=gasPrice[i]/1000000000
            tx.fee= tx.usedGas * tx.gasPrice

            sender.transactionsPool.append(tx)
            FullTransaction.transaction_prop(tx)

    # Transaction propogation & preparing pending lists for miners
    def transaction_prop(tx):
        # Fill each pending list. This is for transaction propogation
        for i in p.NODES:
            if tx.sender != i.id:
                t= tx
                t.timestamp[1] = t.timestamp[1] + Network.tx_prop_delay() # transaction propogation delay in seconds
                i.transactionsPool.append(t)



    def execute_transactions(miner,currentTime):
        transactions= [] # prepare a list of transactions to be included in the block
        limit = 0 # calculate the total block gaslimit
        count=0
        blocklimit = p.Blimit
        miner.transactionsPool.sort(key=operator.attrgetter('gasPrice'), reverse=True)
        pool= miner.transactionsPool

        while count < len(pool):
                if  (blocklimit >= pool[count].gasLimit and pool[count].timestamp[1] <= currentTime):
                    blocklimit -= pool[count].usedGas
                    transactions += [pool[count]]
                    limit += pool[count].usedGas
                count+=1

        return transactions, limit
