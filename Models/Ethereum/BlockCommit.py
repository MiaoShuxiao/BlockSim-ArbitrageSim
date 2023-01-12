from Scheduler import Scheduler
from InputsConfig import InputsConfig as p
from Models.Ethereum.Node import Node
from Statistics import Statistics
from Models.Ethereum.Transaction import LightTransaction as LT, FullTransaction as FT
from Models.Network import Network
from Models.Ethereum.Consensus import Consensus as c
from Models.BlockCommit import BlockCommit as BaseBlockCommit
import random
import copy

class BlockCommit(BaseBlockCommit):

    # Handling and running Events
    def handle_event(event):
        if event.type == "create_block":
            BlockCommit.generate_block(event)
        elif event.type == "receive_block":
            BlockCommit.receive_block(event)

    # Block Creation Event
    def generate_block (event):
        miner = p.NODES[event.block.miner]
        minerId = miner.id
        eventTime = event.time
        blockPrev = event.block.previous

        if blockPrev == miner.last_block().id:
            Statistics.totalBlocks += 1 # count # of total blocks created!
            print(Statistics.totalBlocks)
            if p.hasTrans:
                if p.Ttechnique == "Light": blockTrans,blockSize = LT.execute_transactions(miner,eventTime)
                elif p.Ttechnique == "Full": blockTrans,blockSize = FT.execute_transactions(miner,eventTime)
                p.blockCount+=1
                event.block.transactions = blockTrans
                event.block.usedgas = blockSize
                if(p.blockCount == p.coalitionUpdatePerBlock):
                    p.roundCount += 1
                    p.blockCount = 0
                    BlockCommit.coalitionUpdate()
                    coalitionCount = 0
                    for c in p.COALITIONS:
                        p.COALITIONDETAILS += [[p.roundCount, c.id, c.users, c.winCount, c.totalCount, c.currentRoundBudget, c.currentRoundProfit]]
                        c.currentRoundProfit = 0
                        if(len(c.users) > 0):
                            coalitionCount+=1
                    print("Round:", p.roundCount, "Coalition Count:", coalitionCount)
                    p.COALITIONCOUNTS += [[p.roundCount, coalitionCount]]

            if p.hasUncles:
                BlockCommit.update_unclechain(miner)
                blockUncles = Node.add_uncles(miner) # add uncles to the block
                event.block.uncles = blockUncles #(only when uncles activated)
            pickUpTime = 0
            prevBlockTime = 0
            if blockPrev != -1:
                pickUpTime = miner.blockchain[-1].timestamp

                if blockPrev != 0:
                    prevBlockTime = miner.blockchain[-2].timestamp

            miner.blockchain.append(event.block)

            if p.hasTrans and p.Ttechnique == "Light":LT.create_transactions(pickUpTime, prevBlockTime) # generate transactions
            BlockCommit.propagate_block(event.block)
            BlockCommit.generate_next_block(miner,eventTime)# Start mining or working on the next block

    def coalitionUpdate():
        winnerC = - 1
        winnerProfitRate = -100
        for c in p.COALITIONS:
            if c.currentRoundBudget <= 0:
                continue
            stakerReward = c.currentRoundProfit
            helperReward = 0
            if(c.currentRoundProfit / c.currentRoundBudget > winnerProfitRate):
                winnerProfitRate = c.currentRoundProfit / c.currentRoundBudget
                winnerC = c.id
            if c.currentRoundProfit > 0:
                stakerReward = c.currentRoundProfit * c.splitRate
                helperReward = c.currentRoundProfit * (1 - c.splitRate)
                c.stakerRewardPerUnit = stakerReward / c.currentRoundBudget
                c.avgHelperReward = helperReward / len(c.users)
            for userId in c.users:
                #TODO: Update the profit distribution
                p.USERS[userId].profit = p.USERS[userId].profit + stakerReward * p.USERS[userId].budget / c.currentRoundBudget
                p.USERS[userId].profit = p.USERS[userId].profit + helperReward / len(c.users)
                p.USERS[userId].currentRoundStakeProfit = stakerReward * p.USERS[userId].budget / c.currentRoundBudget
                p.USERS[userId].currentRoundHelperProfit = helperReward / len(c.users)
                p.USERS[userId].currentRoundProfit = stakerReward * p.USERS[userId].budget / c.currentRoundBudget
                p.USERS[userId].currentRoundProfit += (p.USERS[userId].profit + helperReward / len(c.users))
        if winnerC != -1:
            for c in p.COALITIONS:
                if c.id == winnerC:
                    continue
                newC = []
                for u in c.users:
                    prob = random.random()
                    if(prob > p.USERS[u].userMovingProb
                    and p.USERS[u].currentRoundProfit/(p.USERS[u].budget + p.helperUtilityCost) < winnerProfitRate
                    and p.USERS[u].currentRoundProfit - p.COALITIONMOVECOST > 0):
                        p.USERS[userId].profit
                        newC += [u]
                    else:
                        p.COALITIONS[winnerC].users += [u]
                        p.COALITIONS[winnerC].currentRoundBudget += p.USERS[u].budget
                        c.currentRoundBudget -= p.USERS[u].budget
                c.users = copy.deepcopy(newC)

    # Block Receiving Event
    def receive_block (event):

        miner = p.NODES[event.block.miner]
        minerId = miner.id
        currentTime = event.time
        blockPrev = event.block.previous # previous block id


        node = p.NODES[event.node] # recipint
        lastBlockId= node.last_block().id # the id of last block

        #### case 1: the received block is built on top of the last block according to the recipient's blockchain ####
        if blockPrev == lastBlockId:
            node.blockchain.append(event.block) # append the block to local blockchain

            if p.hasTrans and p.Ttechnique == "Full": BaseBlockCommit.update_transactionsPool(node, event.block)

            BlockCommit.generate_next_block(node,currentTime)# Start mining or working on the next block

         #### case 2: the received block is  not built on top of the last block ####
        else:
            depth = event.block.depth + 1
            if (depth > len(node.blockchain)):
                BlockCommit.update_local_blockchain(node,miner,depth)
                BlockCommit.generate_next_block(node,currentTime)# Start mining or working on the next block

            #### 2- if depth of the received block <= depth of the last block, then reject the block (add it to unclechain) ####
            else:
                 uncle=event.block
                 node.unclechain.append(uncle)

            if p.hasUncles: BlockCommit.update_unclechain(node)
            if p.hasTrans and p.Ttechnique == "Full": BaseBlockCommit.update_transactionsPool(node,event.block) # not sure yet.

    # Upon generating or receiving a block, the miner start working on the next block as in POW
    def generate_next_block(node,currentTime):
	    if node.hashPower > 0:
                 blockTime = currentTime + c.Protocol(node) # time when miner x generate the next block
                 Scheduler.create_block_event(node,blockTime)

    def generate_initial_events():
            currentTime=0
            for node in p.NODES:
            	BlockCommit.generate_next_block(node,currentTime)

    def propagate_block (block):
        for recipient in p.NODES:
            if recipient.id != block.miner:
                blockDelay= Network.block_prop_delay() # draw block propagation delay from a distribution !! or you can assign 0 to ignore block propagation delay
                Scheduler.receive_block_event(recipient,block,blockDelay)

    def update_local_blockchain(node,miner,depth):
        # the node here is the one that needs to update its blockchain, while miner here is the one who owns the last block generated
        # the node will update its blockchain to mach the miner's blockchain
        from InputsConfig import InputsConfig as p
        i=0
        while (i < depth):
            if (i < len(node.blockchain)):
                if (node.blockchain[i].id != miner.blockchain[i].id): # and (self.node.blockchain[i-1].id == Miner.blockchain[i].previous) and (i>=1):
                    node.unclechain.append(node.blockchain[i]) # move block to unclechain
                    newBlock = miner.blockchain[i]
                    node.blockchain[i]= newBlock
                    if p.hasTrans and p.Ttechnique == "Full": BaseBlockCommit.update_transactionsPool(node,newBlock)
            else:
                newBlock = miner.blockchain[i]
                node.blockchain.append(newBlock)
                if p.hasTrans and p.Ttechnique == "Full": BaseBlockCommit.update_transactionsPool(node,newBlock)
            i+=1

    # Upon receiving a block, update local unclechain to remove all uncles included in the received block
    def update_unclechain(node):
        ### remove all duplicates uncles in the miner's unclechain
        a = set()
        x=0
        while x < len(node.unclechain):
            if node.unclechain[x].id in a:
                del node.unclechain[x]
                x-=1
            else:
                a.add(node.unclechain[x].id)
            x+=1

        j=0
        while j < len (node.unclechain):
            for k in node.blockchain:
                if node.unclechain[j].id == k.id:
                    del node.unclechain[j] # delete uncle after inclusion
                    j-=1
                    break
            j+=1

        j=0
        while j < len (node.unclechain):
            c="t"
            for k in node.blockchain:
                u=0
                while u < len(k.uncles):
                    if node.unclechain[j].id == k.uncles[u].id:
                        del node.unclechain[j] # delete uncle after inclusion
                        j-=1
                        c="f"
                        break
                    u+=1
                if c=="f":
                    break
            j+=1
