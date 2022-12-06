class User():
    def __init__(self, id = 0, connectedMiner = 0, networkLatency = 0, profit = 0, isHelper = True, isStaker = True):
        self.id = id
        self.connectedMiner = connectedMiner
        self.networkLatency = networkLatency
        self.isHelper = isHelper
        self.isStaker = isStaker
        self.profit = 0