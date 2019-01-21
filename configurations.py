
class GameProperties:
    def __init__(self, namegame, isTesting, RomFolder = 'roms/'):
        self.namegame = namegame
        self.isTesting = isTesting
        self.rompath = RomFolder
        if namegame == 'breakout':
            self.preprocessFrom = 26
            self.preprocessTo = 110
        elif namegame == 'pong':
            self.preprocessFrom = 18
            self.preprocessTo = 102
        elif namegame == 'enduro':
            self.preprocessFrom = 0
            self.preprocessTo = 84
        elif namegame == 'frostbite':
            self.preprocessFrom = 16
            self.preprocessTo = 100
    def GetLimits(self):
        return self.preprocessFrom, self.preprocessTo