import time
import socket
import select
import sys
import string
import indexer
import pickle as pkl
from chat_utils import *
import chat_group as grp
import Corrected as game


class Server:
    def __init__(self):
        self.new_clients = [] #list of new sockets of which the user id is not known
        self.logged_name2sock = {} #dictionary mapping username to socket
        self.logged_sock2name = {} # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        #start server
        self.server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        self.allgame = {}
        #initialize past chat indices
        self.indices={}
        #sonnet indexing
        self.sonnet = indexer.PIndex("AllSonnets.txt")
        self.turn = 0

    def new_client(self, sock):
        #add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)

    def login(self, sock):
        #read the msg that should have login code plus username
        msg = myrecv(sock)
        if len(msg) > 0:
            code = msg[0]

            if code == M_LOGIN:
                name = msg[1:]
                if self.group.is_member(name) != True:
                    #move socket from new clients list to logged clients
                    self.new_clients.remove(sock)
                    #add into the name to sock mapping
                    self.logged_name2sock[name] = sock
                    self.logged_sock2name[sock] = name
                    #load chat history of that user
                    if name not in self.indices.keys():
                        try:
                            self.indices[name]=pkl.load(open(name+'.idx','rb'))
                        except IOError: #chat index does not exist, then create one
                            self.indices[name] = indexer.Index(name)
                    print(name + ' logged in')
                    self.group.join(name)
                    mysend(sock, M_LOGIN + 'ok')
                else: #a client under this name has already logged in
                    mysend(sock, M_LOGIN + 'duplicate')
                    print(name + ' duplicate login attempt')
            else:
                print ('wrong code received')
        else: #client died unexpectedly
            self.logout(sock)

    def logout(self, sock):
        #remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx','wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()

#==============================================================================
# main command switchboard
#==============================================================================
    def handle_msg(self, from_sock):
        #msg is the string sent by the client state machine: IMPORTANT
        msg = myrecv(from_sock)
        if len(msg) > 0:
            code = msg[0]
#==============================================================================
#             handle connect request: this is implemented for you
#==============================================================================
            if code == M_CONNECT:
                to_name = msg[1:]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg = M_CONNECT + 'hey you'
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg = M_CONNECT + 'ok'
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, M_CONNECT + from_name)
                else:
                    msg = M_CONNECT + 'no_user'
                mysend(from_sock, msg)
#==============================================================================
#             handle multicast message exchange; IMPLEMENT THIS
#==============================================================================
            elif code == M_EXCHANGE:

                from_name = self.logged_sock2name[from_sock]
                m = msg[1:]
                print("exchanging message", m)
                # Finding the list of people to send to
                the_guys = self.group.list_me(from_name)[1:]
                for g in the_guys:
                    to_sock = self.logged_name2sock[g]
                    self.indices[g].add_msg_and_index(m)
                    mysend(to_sock, M_EXCHANGE + m)
                self.indices[from_name].add_msg_and_index(m)

            elif code == M_GAME:
                from_name = self.logged_sock2name[from_sock]
                guys = self.group.list_me(from_name)
                self.group.game(from_name)
                found, group_key = self.group.find_group(from_name)
                self.allgame[group_key] = game.Game(guys)
                self.allgame[group_key].start_game()
                m = ''
                m += from_name + "wants to play MONOPOLY. You are in game mode now\n"
                m += 'Enter "ROLL" to roll a dice\n'
                m += 'Enter "QUIT" to quit the game\n'
                m += 'Enter "STATUS" to check the current status\n'
                m += 'The order is:\n'
                m += str(guys)
                for guy in guys:
                    to_sock = self.logged_name2sock[guy]
                    mysend(to_sock, M_EXCHANGE + m)
                    mysend(to_sock, M_TOGAME)

            elif code == M_ROLL:
                print("roll")
                from_name = self.logged_sock2name[from_sock]
                found, group_key = self.group.find_group(from_name)
                g = self.allgame[group_key]
                die = g.roll_the_dice(from_name)
                if type(die) is str:
                    mysend(from_sock, M_EXCHANGE + die)
                elif type(die) is int:
                    newposit = g.move(die, from_name)
                    mapp = g.draw_map()
                    print(type(mapp))
                    guys = self.group.list_me(from_name)
                    mysend(from_sock, M_EXCHANGE + "you got " + str(die))
                    mysend(from_sock, M_EXCHANGE + 'You are in '+ newposit)
                    for guy in guys:
                        to_sock = self.logged_name2sock[guy]
                        #print(to_sock)
                        mysend(to_sock, M_EXCHANGE + mapp)
                    b = g.check_land(from_name, newposit)
                    if b == True:
                        m = ''
                        m += "Do you want to buy the ground?\n"
                        m += 'Enter "BUY" to buy; enter "NO" to give up\n'
                        mysend(from_sock, M_EXCHANGE + m)
                        mysend(from_sock, M_TOBUY)
                    else:
                        mysend(from_sock, M_EXCHANGE + b)
                        tur = g.next_turn()
                        mysend(from_sock, M_EXCHANGE + tur)


            elif code == M_BUY:
                from_name = self.logged_sock2name[from_sock]
                found, group_key = self.group.find_group(from_name)
                g = self.allgame[group_key]
                guys = self.group.list_me(from_name)
                mysend(from_sock, M_EXCHANGE + g.purchase(from_name))
                tur = g.next_turn()

                for guy in guys:
                        to_sock = self.logged_name2sock[guy]
                        mysend(to_sock, M_EXCHANGE + tur)
               
                mysend(from_sock, M_TOGAME)


            elif code == M_NOTBUY:
                from_name = self.logged_sock2name[from_sock]
                found, group_key = self.group.find_group(from_name)
                g = self.allgame[group_key]
                mysend(from_sock, M_EXCHANGE + "You lost such a chance, loser")
                mysend(from_sock, M_TOGAME)
                guys = self.group.list_me(from_name)
                tur = g.next_turn()

                for guy in guys:
                        to_sock = self.logged_name2sock[guy]
                        mysend(to_sock, M_EXCHANGE + tur)

            elif code == M_STATUS:
                from_name = self.logged_sock2name[from_sock]
                found, group_key = self.group.find_group(from_name)
                g = self.allgame[group_key]
                mysend(from_sock, M_EXCHANGE + g.game_status())


            elif code == M_QUITGAME:
                from_name = self.logged_sock2name[from_sock]
                found, group_key = self.group.find_group(from_name)
                guys = self.group.list_me(from_name)

                g = self.allgame[group_key]
                for guy in guys:
                    to_sock = self.logged_name2sock[guy]
                    mysend(to_sock, M_EXCHANGE + g.game_status()+g.winner())
                    mysend(to_sock, M_TOCHAT)
                    self.state = S_CHATTING
         #           mysend(to_sock, M_EXCHANGE + g.quit_game(from_name))
                    
                g.quit_game(from_name)
                
  #              self.group.quit_game(from_name)

#==============================================================================
#             listing available peers; IMPLEMENT THIS
#==============================================================================
            elif code == M_LIST:
                from_name = self.logged_sock2name[from_sock]
                peers = self.group.list_all()
                mysend(from_sock, peers)
#==============================================================================
#             retrieve a sonnet; IMPLEMENT THIS
#==============================================================================
            elif code == M_POEM:
                poem_indx = 0
                poem_indx = int(msg[1:].strip())
                from_name = self.logged_sock2name[from_sock]
                poeml = self.sonnet.get_poem(poem_indx)
                poem = ''
                for i in poeml:
                    poem += i
                    poem += "\n"
                mysend(from_sock, M_POEM + poem)
#==============================================================================
#             retrieve the time; IMPLEMENT THIS
#==============================================================================
            elif code == M_TIME:
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())
                mysend(from_sock, M_TIME + ctime)
#==============================================================================
#             search handler; IMPLEMENT THIS
#==============================================================================
            elif code == M_SEARCH:
                key = msg[1:]
                l = []
                for names in self.indices.keys():
                    indexer = self.indices[names]
                    for mes in indexer.search(key):
                        l.append(mes[1])
                l = set(l)
                mysend(from_sock, M_SEARCH + '\n'.join(l))
#==============================================================================
#             the "from" guy has had enough (talking to "to")!
#==============================================================================
            elif code == M_DISCONNECT:
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, M_DISCONNECT)
#==============================================================================
#                 the "from" guy really, really has had enough
#==============================================================================
            elif code == M_LOGOUT:
                self.logout(from_sock)
        else:
            #client died unexpectedly
            self.logout(from_sock)

#==============================================================================
# main loop, loops *forever*
#==============================================================================
    def run(self):
        print ('starting server...')
        while(1):
           read,write,error=select.select(self.all_sockets,[],[])
           print('checking logged clients..')
           for logc in list(self.logged_name2sock.values()):
               if logc in read:
                   self.handle_msg(logc)
           print('checking new clients..')
           for newc in self.new_clients[:]:
               if newc in read:
                   self.login(newc)
           print('checking for new connections..')
           if self.server in read :
               #new client request
               sock, address=self.server.accept()
               self.new_client(sock)

def main():
    server=Server()
    server.run()

main()
