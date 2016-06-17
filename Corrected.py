import random


class Game():
    def __init__(self, players):
        self.players = players
        self.mapstate = {}
        #all fields with a list of players on it as value
        self.playerlocation = {}
        #players with the name of field thay are at as values
        self.linmap = []
        #linear representation of the map to monitor moves
        self.money  = {}
        # player : money
        self.assets = {}
        # player : list of assets
        self.propprice = {}
        #increments each move; resets to 0 when reaches the number of players
        self.turn = 0
        #a bunch of cities, from which the names will be randomly chosen
        self.fileofcities = open('list.txt', 'r')



    def start_game(self):
        #MAP GENERATOR
        self.linmap = ['START']
        licities = self.fileofcities.readlines()
        li = licities

        # 12 randomly chosen city names
        for a in range(15):
            indx = random.randrange(0, len(li), +1)
            city = li[indx].rstrip()
            self.linmap.append(city)
            li.remove(li[indx])
        for city in self.linmap:
            self.mapstate[city] = []
        price = 40
        counter = 0
        # Assign prices to all fields:
        # Price increases by 20 every two fields
        # EXAMPLE: ( 1 and 2 are 40, 2 and 3 are 60 etc)
        for city in self.linmap:
            if city == self.linmap[0]:
                counter-=1
                pass
            if counter == 2:
                price+=20
                counter = 0
                self.propprice[city] = price
            else:
                self.propprice[city] = price
            counter+=1
        #    MONEY, Assets DISTRIBUTION /// mapping location
        #    of player to their location and map to the players
        for p in self.players:
            self.money[p] = 300
            self.assets[p] = []
            self.playerlocation[p] = self.linmap[0]
            self.mapstate[self.linmap[0]].append(p)

    def game_status(self):
        full = ''
        assets = ''
        full += 'Players assets and cash: \n\
        ---------------------------------- \n'
        for player in self.players:
            assets = ''
            for asset in self.assets[player]:
                assets += asset+ '; '
            full +=player + ' owns: ' + str(self.money[player])
            full +='$ and these grounds: ' + str(assets) + '\n'
            full +=player+' is located at: '+self.playerlocation[player]+'\n'
        full += "MAP: \n\
        -----------------------------------\n" + str(self.draw_map())
        return full

    def roll_the_dice(self, name):
        if name == self.players[self.turn]:
            die = random.randint(1, 6)
            return die
        else:
            die = 'It is not your turn, '+ str(name)
            return die
    def next_turn(self):
        who = ''
        if self.turn == len(self.players)-1:
            self.turn = 0
        else:
            self.turn+=1

        who = str(self.players[self.turn]) + '\'s Turn to play'
        return who

    def move(self, die, name): 

        prevposition = self.playerlocation[name]
        b4field = self.mapstate[prevposition]
        #not sure 'bout this line
        b4field.remove(name)
        indx_of_prevpos = self.linmap.index(prevposition)
        #changing the state of previous position

        moveto = indx_of_prevpos + int(die)
        #If the next position is going through start
        if moveto > len(self.linmap)-1:
            self.new_round(name)
            indx_newposition = moveto - len(self.linmap)
        else:
            indx_newposition = moveto
        newposit = self.linmap[indx_newposition]
        self.playerlocation[name] = newposit
        self.mapstate[newposit].append(name)
        return newposit

    def new_round(self, name):
        self.money[name] += 200

    def check_land(self, name, field):
        for key, value in self.assets.items():
            if field in value:
                if name == key:
                    return str('This is your land')
                elif name != key:
                    landlord = key
                    self.pay_fine(name, landlord)
                    return str('You payed a fine to ' + landlord)
        return True
                

    def purchase(self, name):
        if self.playerlocation[name] == 'START':
            b = 'Why are you trying to buy START? It is worthless!!!'
        elif self.money[name] >= self.propprice[self.playerlocation[name]]:
             self.assets[name].append(self.playerlocation[name])
             self.money[name] = self.money[name] - self.propprice[self.playerlocation[name]]
             b = self.playerlocation[name] + ' Purchased!'
        else:
            b = 'You do not have enough money, NEXT turn' 
        print(self.mapstate)
        print(self.propprice)
        return b
        
    def pay_fine(self, name, landlord):
        fine = int(self.propprice[self.playerlocation[name]]//4)
        if self.money[name] >= fine:    
            self.money[name] -= fine
            self.money[landlord] += fine
        else:
            self.lose_game(name)

    def draw_map(self):
        m = ''
        for city in self.linmap:
            
            m+= city + ' hosts  ' + str(self.mapstate[city])+ ' and costs ' + str(self.propprice[city]) +'$\n'
        return m


    def lose_game(self, name):
        a = 'The player '+name+' got bankrupt.\n \
            He was found under a bridge in downtown \
            of ' + self.playerlocation[name]+'\n It\'s a terrible, \
            terrible loss...'
        self.mapstate[self.playerlocation[name]].remove(name)
        del self.assets[name]
        del self.playerlocation[name]
        self.players.remove(name)
        self.money[name] = 'Lost'
        return a

    def quit_game(self, name):
        del self.mapstate[self.playerlocation[name]]
        del self.assets[name]
        del self.playerlocation[name]
        self.players.remove(name)

        

    def winner(self):
        w = ''
        mx = 0
        for c in self.money.values():
            if int(c)>=mx:
                mx = int(c)
        for a, b in self.money.items():
            if b == mx:
                w += 'The winner is: '+str(a)+" with "+str(b)+"$ \n"

        return w
        
        
if __name__ == "__main__":
    pl = ['aa', 'bb', 'cc', 'dd']
    g = Game(pl)
    g.start_game()
    g.move(3, 'aa')
    g.purchase('aa')
    print(g.game_status())
    g.move(3, 'cc')
    print(g.check_land('cc', g.playerlocation['cc']))
    print(g.draw_map())
    print(g.game_status())
    g.move(5, 'cc')
