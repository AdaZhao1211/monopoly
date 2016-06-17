S_ALONE = 0
S_TALKING = 1
S_GAMING = 2

#==============================================================================
# Group class:
# member fields:
#   - An array of items, each a Member class
#   - A dictionary that keeps who is in a chat group or game group
# member functions:
#    - join: first time in
#    - leave: leave the system, and the group
#    - list_my_peers: who is in chatting with me?
#    - list_all: who is in the system, and the chat groups
#    - connect: connect to a peer in a chat group, and become part of the group
#    - disconnect: leave the chat group but stay in the system
#    - game: join a game from chat
#    - quit_game: quit a game to chat
#==============================================================================

class Group:

    def __init__(self):
        self.members = {}
        self.chat_grps = {}
        #add game_grps to record groups that are in game
        self.game_grps = {}
        self.grp_ever = 0

    def join(self, name):
        self.members[name] = S_ALONE
        return

    def is_member(self, name):
        return name in self.members.keys()

    def leave(self, name):
        self.disconnect(name)
        del self.members[name]
        return

    def find_group(self, name):
        found = 0
        group_key = 0
        for k in self.chat_grps.keys():
            if name in self.chat_grps[k]:
                found = 1
                group_key = k
                break
        for k in self.game_grps.keys():
            if name in self.game_grps[k]:
                found = 2
                group_key = k
                break
        return found, group_key

    def connect(self, me, peer):
        peer_in_group = 0
        #if peer is in a group, join her group
        peer_in_group, group_key = self.find_group(peer)
        if peer_in_group == 1:
            print(peer, "is talking already, connect!")
            self.chat_grps[group_key].append(me)
            self.members[me] = S_TALKING
        elif peer_in_group == 0:
            # otherwise, create a new group with you and her
            print(peer, "is idle as well")
            self.grp_ever += 1
            group_key = self.grp_ever
            self.chat_grps[group_key] = []
            self.chat_grps[group_key].append(me)
            self.chat_grps[group_key].append(peer)
            self.members[me] = S_TALKING
            self.members[peer] = S_TALKING
        elif peer_in_group == 2:
            print("not able to connect")
            #if the person is playing a game

        return

    def disconnect(self, me):
        # find myself in the group, quit
        in_group, group_key = self.find_group(me)
        if in_group == 1:
            self.chat_grps[group_key].remove(me)
            self.members[me] = S_ALONE
            # peer may be the only one left as well... handle this case
            if len(self.chat_grps[group_key]) == 1:
                peer = self.chat_grps[group_key].pop()
                self.members[peer] = S_ALONE
                del self.chat_grps[group_key]
        return

    def game(self, me):
        me_in_group, group_key = self.find_group(me)
        if me_in_group==1:
            self.game_grps[group_key] = self.chat_grps.pop(group_key)
            for member in self.game_grps[group_key]:
                self.members[member] = S_GAMING
        return

    def quit_game(self, me):
        me_in_group, group_key = self.find_group(me)

        if me_in_group==2:
            self.chat_grps[group_key] = self.game_grps.pop(group_key)
            for member in self.chat_grps[group_key]:
                self.members[member] = S_TALKING
        return

    def list_all(self):
        # a simple minded implementation
        full_list = "Users: ------------" + "\n"
        full_list += str(self.members) + "\n"
        full_list += "Groups: -----------" + "\n"
        full_list += str(self.chat_grps) + "\n"
        full_list += "Groups in game: ---" + "\n"
        full_list += str(self.game_grps) + "\n"
        return full_list

    def list_all2(self):
        print("Users: ------------")
        print(self.members)
        print("Groups: -----------")
        print(self.chat_grps)
        print("Groups in game: ---")
        print(self.game_grps,'\n')
        member_list = str(self.members)
        grp_list = str(self.chat_grps)
        return member_list, grp_list

    def list_me(self, me):
        # return a list, "me" followed by other peers in my group
        if me in self.members.keys():
            my_list = []
            my_list.append(me)
            in_group, group_key = self.find_group(me)
            if in_group == 1:
                for member in self.chat_grps[group_key]:
                    if member != me:
                        my_list.append(member)
            if in_group == 2:
                for member in  self.game_grps[group_key]:
                    if member != me:
                        my_list.append(member)
        return my_list

if __name__ == "__main__":
    g = Group()
    g.join('a')
    g.join('b')
    g.list_all2()
    g.connect('a', 'b')
    g.list_all2()
    g.game('a')
    g.list_all2()
    g.join('c')
    g.quit_game('b')
    g.list_all2()
