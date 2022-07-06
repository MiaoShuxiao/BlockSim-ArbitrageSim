from Models.Node import Node as BaseNode

class Coalition():
    def __init__(self, id = 0, users = [], probRate = 0, winCount = 0, totalCount = 0):
        self.id = id
        self.users = users
        self.probRate = probRate
        self.winCount = winCount
        self.totalCount = totalCount
