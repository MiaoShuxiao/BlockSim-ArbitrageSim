class User():
    def __init__(self, id = 0, connectedMiner = 0, networkLatency = 0, profit = 0, winCount = 0, gameCount = 0):
        self.id = id
        self.connectedMiner = connectedMiner
        self.networkLatency = networkLatency
        self.profit = 0
        self.winCount = 0
        self.gameCount = 0