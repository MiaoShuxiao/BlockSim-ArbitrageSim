class User():
    def __init__(self, id = 0, connectedMiner = 0, budget = 0, profit = 0, isHelper = True, isStaker = True, currentRoundWinPoint = 0, currentRoundProfit = 0):
        self.id = id
        self.connectedMiner = connectedMiner
        self.isHelper = isHelper
        self.isStaker = isStaker
        self.budget = budget
        self.profit = profit
        self.currentRoundWinPoint = currentRoundWinPoint
        self.currentRoundProfit = currentRoundProfit