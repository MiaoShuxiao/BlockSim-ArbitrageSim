class Coalition():
    def __init__(self, id = 0, users = [], splitRate = 0.5, probRate = 0, winCount = 0, totalCount = 0, currentRoundBudget = 0, currentRoundProfit = 0):
        self.id = id
        self.users = users
        self.splitRate = splitRate
        self.probRate = probRate
        self.winCount = winCount
        self.totalCount = totalCount
        self.currentRoundBudget = 0
        self.currentRoundProfit = 0
        self.totalPointCount = 0 ## TODO: for multiple security level implementation