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

        if pickUpTime == 0 or prevTime == 0:
            mean = random.randint(0, p.Binterval) * p.Tn
        # little trick to generate genesis transactions
        if mean == 0:
            mean = 1
        Psize= round(random.expovariate(1 / mean))
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
            tx.gasPrice = random.expovariate(1/100)
            tx.profit = random.expovariate(1/(10 ** 16))

            participants = []
            test =[]
            for j in p.COALITIONS:
                if j.users == []:
                    continue
                prob = random.random()
                if(prob < j.probRate and j.users != []):
                    participants += [j]
                    for u in j.users:
                        p.USERS[u].gameCount += 1

            if len(participants) > 1:
                txGroup = LightTransaction.create_auction(participants, tx, prevTime, pickUpTime)
                LightTransaction.pool += txGroup
            elif len(participants) == 1:
                tx.fee= tx.usedGas * tx.gasPrice
                LightTransaction.pool += [tx]
                for u in participants[0].users:
                    p.USERS[u].profit += ((tx.profit - tx.gasPrice * tx.usedGas) / len(participants[0].users))
            else:
                for u in participants[0].users:
                    p.USERS[u].profit += ((tx.profit - tx.gasPrice * tx.usedGas) / len(participants[0].users))
                p.USERS[tx.sender].profit += (tx.profit - tx.gasPrice * tx.usedGas)

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
                calculateLatency = copy.deepcopy(p.USERLATENCY)
                for receiver in p.USERS:
                    calculateLatency[receiver.id] += latency[receiver.connectedMiner]
                delay_time = min(calculateLatency[calculateLatency > 0])
                if minLatency < delay_time:
                    selectedUser = copy.deepcopy(u)
                    minLatency = copy.deepcopy(delay_time)
                    selectedLatency = copy.deepcopy(calculateLatency)
            coalitionDict[c1.id] = (copy.deepcopy(selectedUser), copy.deepcopy(selectedLatency))
        prevCoalition = random.choice(participants)
        tx.sender = random.choice(prevCoalition.users)
        auctionResult = LightTransaction.execute_auction(participants, tx, prevCoalition, pickUpTime, coalitionDict)
        txGroup = LightTransaction.calculate_result(auctionResult)
        return txGroup


    def execute_auction(participants, tx, prevCoalition, pickUpTime, coalitionDict):
        count = 0
        bids = PriorityQueue()
        latestTxFromCoalition = {}
        latestTxFromCoalition[prevCoalition.id] = copy.deepcopy(tx)
        bids.put((tx.receiveTime, count, tx, prevCoalition))
        currentTime = tx.receiveTime
        while currentTime < pickUpTime:
            if(bids.empty()):
                break
            currBid = bids.get()
            currCoalition = currBid[3]
            currentTime = currBid[2].receiveTime
            #print("currentTime: ", currentTime, " currentBid: ", currBid[2].gasPrice)
            latestTxFromCoalition[currCoalition.id] = copy.deepcopy(currBid[2])
            for c in participants:
                if currCoalition.id == c.id:
                    continue
                #print("DICT:",coalitionDict)
                #TODO: 2 parameters: node number, text file - n个 有n * 2n个数据， 分别是（均值，方差）
                listener = coalitionDict[currCoalition.id][1]
                listenDelay = abs(min(listener[c.users]))
                if ((c.id not in latestTxFromCoalition) or (latestTxFromCoalition[c.id].gasPrice < currBid[2].gasPrice)):
                    if((currBid[2].gasPrice * currBid[2].usedGas * 1.2 < currBid[2].profit)):
                        newBid = copy.deepcopy(currBid[2])
                        newBid.gasPrice = newBid.gasPrice * 1.15
                        newBid.fee= newBid.usedGas * newBid.gasPrice
                        newBid.sender = coalitionDict[c.id][0]
                        newBid.to = p.USERS[newBid.sender].connectedMiner
                        newBid.receiveTime = currentTime + listenDelay + p.USERLATENCY[newBid.sender]

                        count+=1
                        bids.put((copy.deepcopy(newBid.receiveTime), count, copy.deepcopy(newBid), copy.deepcopy(c)))
        return latestTxFromCoalition

    def calculate_result(resultDict):
        winner = -1
        winnerGasPrice = -99999
        toBeExecuted = []
        for c in resultDict:
            p.COALITIONS[c].totalCount += 1
            if(resultDict[c].gasPrice > winnerGasPrice):
                winner = c
                winnerGasPrice = resultDict[c].gasPrice

        for c in resultDict:
            if(c == winner):
                p.COALITIONS[c].winCount += 1
                resultDict[c].profit = 0
                for u in p.COALITIONS[c].users:
                    p.USERS[u].profit += ((resultDict[c].profit - resultDict[c].gasPrice * resultDict[c].usedGas) / len(p.COALITIONS[c].users))
                    p.USERS[u].winCount += 1
            else:
                for u in p.COALITIONS[c].users:
                    #TODO: move 0.2 (LOSS RATE) to the config file
                    #run multiple time sim and take average
                    #KEEP THE RAW DATA FILES
                    #TODO: HOW TO SPLIT THE PROFIT? GAME THEORY - INCENTIVE MECHANISM, DEPEND ON THE CONTRIBUTIONS
                    # HELPER, BUDGET, LOCATION
                    #TODO: GRAPH - NUMBER OF COALITION / TIME
                    #TODO: GRAPH - REVENUE PER COALITION / REVENUE PER USERS
                    p.USERS[u].profit -= resultDict[c].gasPrice * resultDict[c].usedGas * 0.2 / len(p.COALITIONS[c].users)
            toBeExecuted += [resultDict[c]]
        return toBeExecuted


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
