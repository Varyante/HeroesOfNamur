# -*- coding: utf-8 -*-
import termcolor, random
import saver as s
import multiplayer_module as mm
from colorama import init
init()


# INITIALIZATION


def play_game(map_adress, player_1, player_2, remote_IP=None):
    """
    Main function, manages the global course of in-game events

    Parameters
    ----------
    map_adress: Path of file with map informations (str)
    player_1: type of player 1 (str)
    player_2: type of player 2 (str)
    remote_IP: IP of the computer where remote player is (str)(optional)

    Notes
    -----
    player_1 and player_2 should be 'ia' or 'player'

    Version
    -------
    specification: Mouchet Antoine, Willemart Blandine (v1 08/03/19)

    """
    #CONNECT TO OTHER PLAYER 
    if player_1 == 'away':
        connection = mm.connect_to_player(1, remote_IP)
    elif player_2 == 'away':
        connection = mm.connect_to_player(2, remote_IP)
    else:
        connection = None

    s.save_initiate(map_adress)

    data_base = generate_db(map_adress)
    new_hero(data_base, player_1, player_2, connection)
    #Keep playing until game ends
    while data_base['nb_turns_afk'] <= 40 and data_base['nb_turns_on_hill'] != data_base['nb_turns_to_win']:
        #Display board
        display_board(data_base)
        #Get orders
        h_attack, h_move = actions_player(data_base, player_1, player_2, connection)
        #Clear board
        clear_board(data_base)
        #get attacks and moves of monsters
        m_attack, m_move = clear_monster_command_sentence(data_base, actions_monsters(data_base))
        #attacks
        basic_attack(data_base, h_attack, m_attack)
        #moves
        movements(data_base, h_move, m_move)
        #Display + xp
        display_board(data_base)
        end_turn(data_base)


    display_endgame(data_base)

    if player_1 =='away' or player_2 =='away':
       mm.disconnect_from_player(connection)

def generate_db(map_adress):
    """
    Returns data base of the game with informations about the classes and board

    Parameters
    ----------
    map_adress: path of file containing map informations (str)

    Returns
    -------
    data_base: dict with all informations about the game (dict)

    Version
    --------
    specification: Antoine Mouchet (v1 19/03/19)
    implementation: Antoine Mouchet (v1 19/03/19)
    """
    data_base = {
        'hill':[],
        'spawns':{},
        'heroes':{},
        'monsters':{},
        'nb_turns_on_hill': 0,
        'nb_turns': 0,
        'nb_turns_afk': 0,
        'damage_dealed': False,
        'color_win':'',
        'classes':{
            #STATS:[level1, level2,..., level5]
            #BARBARIAN STATS
            'barbarian':{'hp_max':[10, 13, 16, 19, 22], 'damage':[2, 3, 4, 5, 6], 'icon': '  \u2694',
                         'energise':{'range':[0, 1, 2, 3, 4], 'ratio':[0, 1, 1, 2, 2], 'cooldown':[0, 1, 1, 1, 1]},
                         'stun':{'range':[0, 0, 1, 2, 3], 'ratio':[0, 0, 1, 2, 3], 'cooldown':[0, 0, 1, 1, 1]}},

            #HEALER STATS
            'healer':{'hp_max':[10, 11, 12, 13, 14], 'damage':[2, 2, 3, 3, 4], 'icon': '  \u2695',
                     'invigorate':{'range':[0, 1, 2, 3, 4], 'ratio':[0, 1, 2, 3, 4], 'cooldown':[0, 1, 1, 1, 1]},
                     'immunise':{'range':[0, 0, 1, 2, 3], 'ratio':[0, 0, 0, 0, 0], 'cooldown':[0, 0, 3, 3, 3]}},

            #MAGE STATS 
            'mage':{'hp_max':[10, 12, 14, 16, 18], 'damage':[2, 3, 4, 5, 6], 'icon': '  \u269b',
                     'fulgura':{'range':[0, 1, 2, 3, 4], 'ratio':[0, 3, 3, 4, 4], 'cooldown':[0, 1, 1, 1, 1]},
                     'ovibus':{'range':[0, 0, 1, 2, 3], 'ratio':[0, 0, 1, 2, 3], 'cooldown':[0, 0, 3, 3, 3]}},

            #ROGUE STATS
            'rogue':{'hp_max':[10, 12, 14, 16, 18], 'damage':[2, 3, 4, 5, 6], 'icon': '  \u2020',
                     'reach':{'range':[0, 1, 2, 3, 4], 'ratio':[0, 0, 0, 0, 0], 'cooldown':[0, 1, 1, 1, 1]},
                     'burst':{'range':[0, 0, 1, 2, 3], 'ratio':[0, 0, 1, 2, 3], 'cooldown':[0, 0, 1, 1, 1]}}
                    }
            }
    
    create_board(map_adress, data_base)
    return data_base


def create_board(path, data_base):
    """
    Extracts informations from file at path and inserts it in the dictionary data base.

    Parameters
    ----------
    path: path of file with info (str)
    data_base: dico with all informations about the game (dict)

    Version
    -------
    specification: Mouchet Antoine, Willame Simon, Willemart Blandine (v1 01/03/19)
    implementation: Mouchet Antoine, Willame Simon, Willemart Blandine (v1 15/03/19)

    """
    map_path = open(path, 'r')
    map_info = map_path.readlines()
    line_id = 0

    map_path.close()

    for line in map_info:
        #Check if line is about map
        if 'map' in line:
            map_infos = map_info[line_id+1]

        #Check if line is now speaking about spawn
        elif 'spawn' in line:
            spawn_coords = []
            id = line_id
            while not 'spur' in map_info[id]:
                if not 'spawn' in map_info[id]:
                    spawn_coords.append(map_info[id])
                id += 1

        #Check if line is now speaking about spur
        elif 'spur' in line:
            spur_coords = []
            id = line_id
            while not 'creatures' in map_info[id]:
                if not 'spur' in map_info[id]:
                    spur_coords.append(map_info[id])
                id += 1

        #Check if line is now speaking about creatures
        elif 'creatures' in line:
            creatures_coords = []
            id = line_id
            while id < len(map_info):
                if not 'creatures' in map_info[id]:
                    creatures_coords.append(map_info[id])
                id += 1
        line_id += 1

    #Place info about map in dictionary
    map_infos = map_infos.split(' ')
    data_base['board'] = [int(map_infos[0]), int(map_infos[1])]
    data_base['nb_turns_to_win'] = int(map_infos[2])

    #Add monsters to dictionary
    for creature in creatures_coords:
        creature_info = creature.split(' ')
        data_base['monsters'][creature_info[0]] = {'position':[int(creature_info[1]), int(creature_info[2])],\
                                                   'hp':int(creature_info[3]), 'damage':int(creature_info[4]), \
                                                   'range':int(creature_info[5]),'xp':int(creature_info[6]),\
                                                   'bonus': 0, 'status': 'neutral', 'status_turn': 0}

    #Add spawn to dictionary
    color_id = 0
    for spawn in spawn_coords:
        spawn_info = spawn.split(' ')
        if color_id == 1:
            data_base['spawns']['blue'] = [int(spawn_info[0]), int(spawn_info[1])]
        else:
            data_base['spawns']['red'] = [int(spawn_info[0]), int(spawn_info[1])]
        color_id += 1

    #Add hill to dictionary
    for spur in spur_coords:
        spur_info = spur.split(' ')
        data_base['hill'].append([int(spur_info[0]), int(spur_info[1])])


def add_hero(hero, team_color, data_base):
    """
    Add hero in dictionary.

    Parameters
    ----------
    hero: informations about the hero (list)
    color: team's color of the hero (str)
    data_base: dictionary with all game informations (dict) 

    Version
    -------
    specification: Mouchet Antoine, Willame Simon, Willemart Blandine (v1 01/03/19)
                   Mouchet Antoine, Willame Simon, Willemart Blandine (v2 09/03/19)
    implementation: Blandine Willemart (v1 13/03/19)

    """
    #Get name and class of hero
    hero_name = hero[0]
    hero_class = hero[1]
    #Add hero in the dictionary
    data_base['heroes'][hero_name] = {'position':data_base['spawns'][team_color],'class': hero_class, \
        'hp': data_base['classes'][hero_class]['hp_max'][0], \
        'level': 1, 'xp': 0, 'team': team_color, 'cooldown1':0, 'cooldown2': 0, \
        'status': 'neutral', 'status_turn': 0, 'bonus': 0}


def new_hero(data_base, player_1, player_2, connection=None):
    """
    Ask heroes informations and calls add_hero to insert them in dictionary.

    Parameters
    ----------
    data_base: dictionary with all game informations (dict)
    player_1: type of player 1 (str)
    player_2: type of player 2 (str)
    connection: sockets to receive/send orders(tuple)(optional)

    Notes
    -----
    player_1 and player_2 should be 'ia' or 'player' or 'away'


    Version
    -------
    specification: Mouchet Antoine, Willame Simon, Willemart Blandine (v1 01/03/19)
    implementation: Antoine Mouchet, Simon Willame (v1 13/03/19)

    """
    heroes_names = []
    for team in ['red','blue']:
        #Ask to player the name_heroes:class and split it into a list
        sentence_is_correct = False
        while not sentence_is_correct:

            #Check if both players are ia
            if player_1 == 'ia' and player_2 == 'ia':
                if team == 'red':
                    heroes_sentence = 'Pumbaa:barbarian Rafiki:mage Zazu:healer Timon:rogue'
                if team == 'blue':
                    heroes_sentence = 'Niels:barbarian Olaf:mage Sven:healer Elsa:rogue'
            
            #Check if one player is an ia
            elif (player_1 == 'ia' and team == 'red') or (player_2 == 'ia' and team == 'blue'):
                heroes_sentence = 'sora:barbarian riku:mage kairi:healer zazu:rogue'

                #Check if other player is away
                if player_1 == 'away' or player_2 == 'away':
                    mm.notify_remote_orders(connection, heroes_sentence)

            #Get orders from other player 
            elif (player_1 == 'away' and team == 'red') or (player_2 == 'away' and team == 'blue'):
                heroes_sentence = mm.get_remote_orders(connection)

            #Both players are humans
            else:
                heroes_sentence = str(input('%s team, please write your 4 heroes and their class (Don\'t forget to write it: name_hero_1:class ...)\n' % team))

            s.save_command(heroes_sentence, team, data_base['nb_turns'])

            heroes_sentence_first_division = heroes_sentence.split( )
            #Crush old variable
            heroes_sentence = []
            for heroes_division in heroes_sentence_first_division:
                heroes_sentence.append(heroes_division.split(':'))

            #Check if there are 4 heroes in team
            if len(heroes_sentence) == 4:
                sentence_is_correct = True
            
                for check_name in range(4):
                    #Check if the class exists
                    if not heroes_sentence[check_name][1] in ['barbarian','rogue','healer','mage']:
                        sentence_is_correct = False

                    #Check if there is no number in the name
                    for number_to_check in range(10):
                        if str(number_to_check) in heroes_sentence[check_name][0]:
                            sentence_is_correct = False

                    #Check that name is not already used
                    if heroes_sentence[check_name][0] in heroes_names:
                        sentence_is_correct = False
            else:
                sentence_is_correct = False

            if sentence_is_correct == False:
                print('Sorry, you made a mistake while creating your heroes. Please try again.')
            #Add names to the list of name already used.
            else:
                for name_id in range(4):
                    heroes_names.append(heroes_sentence[name_id][0])

        #Add the heroes in the data_base
        for character in heroes_sentence:
            add_hero(character, team, data_base)


# DISPLAY AND REFRESH


def display_board(data_base):
    """
    Display board as a string with special icons for the different entities.

    Parameters
    ----------
    data_base: dictionary with all game informations (dict)

    Version
    -------
    specification: Mouchet Antoine, Willame Simon, Willemart Blandine (v2 07/03/19)
    implementation: Mouchet Antoine (v1 07/03/19)

    """
    board = ''
    positions_occupied = []
    #Initialize variables for monsters icons
    monsters_icons = ['  \u2730', '  \u2736', '  \u2732', '  \u2733', '  \u2734', '  \u2735', '  \u2731', '  \u2737', '  \u2738', '  \u2739']
    monster_id = 0

    for row in range(data_base['board'][0]):
        for column in range(data_base['board'][1]):
            #Define position checking
            coords = [row + 1, column + 1]
    
            #Numerize each line
            if column == 0:
                board += str(row +1)
                if row + 1 < 10:
                    board += '   '
                else:
                    board += '  '

            #Loop on positon of heroes
            for heroes_names in data_base['heroes']:
                #Check if a hero is on the case and if hero is alive
                if coords == data_base['heroes'][heroes_names]['position'] and check_hp(data_base, heroes_names, 'heroes') and coords not in positions_occupied:
                    #If hero on case, get the icon associated to his class
                    hero_class = data_base['heroes'][heroes_names]['class']
                    board += termcolor.colored(data_base['classes'][hero_class]['icon'], data_base['heroes'][heroes_names]['team'])
                    #Add coord to list of heroes positions
                    positions_occupied.append(coords)
            
            #Loop on positions of monsters
            for monster_name in data_base['monsters']:
                if coords == data_base['monsters'][monster_name]['position'] and check_hp(data_base, monster_name, 'monsters'):
                    board += termcolor.colored(monsters_icons[monster_id], 'green')
                    #Increase id of monster by 1
                    monster_id += 1
                    positions_occupied.append(coords)
                    #Check there will be enough monster icon, reset monster id if not
                    if monster_id >= 10:
                        monster_id = 0
                    

            #Check if there is no hero or monster on the case
            if coords not in positions_occupied:

                #Loop on positions of spawns
                for team_color in data_base['spawns']:
                    if coords == data_base['spawns'][team_color]:
                        board += termcolor.colored('  \u271a', team_color)
                        positions_occupied.append(coords)

                #Checks if case is a case of the hill
                if coords in data_base['hill']:
                    board += termcolor.colored('  \u2691', 'magenta')
                    
                #Add the usual case skin if nothing on it.
                elif coords not in positions_occupied:
                    board += '  \u25cc'
        board += '\n'

    #Display title
    display_title(data_base)
    #Display board
    print(board)
    #Display stats of entities
    display_stats(data_base)


def display_stats(data_base):
    """
    Displays informations of heroes and monsters

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)

    Version
    --------
    specification: Antoine Mouchet (v1 11/03/19)
    implementation: Antoine Mouchet (v1 11/03/19)

    """
    #Initialize list of blue heroes
    blue_heroes = []

    print(termcolor.colored('HEROES', 'yellow'))
    #loop on heroes
    for hero_name in data_base['heroes']:
        #Display red hero's information
        if data_base['heroes'][hero_name]['team'] == 'red':
            print(termcolor.colored('%s (%s): -Position: %s -Health points: %d -Level: %d (%d exp) -Bonus: %d -Status: %s' % \
                (hero_name, data_base['heroes'][hero_name]['class'], str(data_base['heroes'][hero_name]['position']), \
                 data_base['heroes'][hero_name]['hp'], \
                 data_base['heroes'][hero_name]['level'], data_base['heroes'][hero_name]['xp'], \
                 data_base['heroes'][hero_name]['bonus'], data_base['heroes'][hero_name]['status']), \
                data_base['heroes'][hero_name]['team']))
        elif data_base['heroes'][hero_name]['team'] == 'blue':
            blue_heroes.append(hero_name)

    #Loop on heroes
    for hero_name in blue_heroes:
        #Display blue hero's informations
        print(termcolor.colored('%s (%s): -Position: %s -Health points: %d -Level: %d (%d exp) -Bonus: %d -Status: %s' %\
        (hero_name, data_base['heroes'][hero_name]['class'], str(data_base['heroes'][hero_name]['position']), \
        data_base['heroes'][hero_name]['hp'], \
        data_base['heroes'][hero_name]['level'], data_base['heroes'][hero_name]['xp'], \
        data_base['heroes'][hero_name]['bonus'], data_base['heroes'][hero_name]['status']),\
        data_base['heroes'][hero_name]['team']))

    print(termcolor.colored('MONSTERS', 'yellow'))
    #Loop on monsters
    for monster in data_base['monsters']:

        #Display monster's informations
        print(termcolor.colored('%s: -Position: %s -Health points: %d -Damage: %d -Victory points: %d -Bonus: %d -Status: %s' % \
        (monster, str(data_base['monsters'][monster]['position']), data_base['monsters'][monster]['hp'], \
        data_base['monsters'][monster]['damage'], data_base['monsters'][monster]['xp'], \
        data_base['monsters'][monster]['bonus'], data_base['monsters'][monster]['status']), 'green'))


def display_title(data_base):
    """
    Display title with turn information

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)

    Version
    -------
    Specification: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)

    """
    title = 'Turn: %d   -~-Heroes of Namur-~-' % (data_base['nb_turns'])

    if data_base['nb_turns'] < 20:
        title += '   Number of turns left before hill: %d' % (20-data_base['nb_turns'])
    else:
        title += '   Number of turns on hill: %d' % (data_base['nb_turns_on_hill'])

    print(title)
    

def check_hp(data_base, entity_name, entity_type):
    """
    Returns true if entity is alive

    Parameters
    ----------
    data_base: dictionary with all game informations (dict)
    entity_name: the name of the entity (str)
    entity_type: the type of the entity (str)

    Returns
    -------
    alive: True if hp > 0 (bool)

    Notes
    ------
    entity_type must be either monsters or heroes

    Version
    -------
    specification: Mouchet Antoine, Willame Simon, Willemart Blandine (v2 08/03/19)
    implementation: Mouchet Antoine, Willemart Blandine (v1 08/03/19)

    """
    #Checks that hps of entities are superior than 0.
    if data_base[entity_type][entity_name]['hp'] > 0:
        return True

    #False when entity is dead
    return False


def give_xp(data_base):
    """
    Add monster's victory point (called xp) to heroes who defeated it in their victory point stat

    Parameters
    ----------
    data_base: dictionary with all game informations (dict)

    Version
    -------
    specification: Mouchet Antoine, Willame Simon, Willemart Blandine (v1 01/03/19)
    implementation: Antoine Mouchet (v1 19/03/19)

    """
    #Loop on monsters in data base
    for monster in data_base['monsters']:

        #Check if monster is dead
        if not check_hp(data_base, monster, 'monsters') and data_base['monsters'][monster]['xp'] != 0:
            #Get names of heroes in range of monster
            heroes_in_range = check_in_range_monster(monster, data_base)
            #Get number of heroes in range of monster
            nb_heroes = len(heroes_in_range)
            #Get xp given by monster when killed
            monster_xp = data_base['monsters'][monster]['xp']

            #Check that there is at least one hero alive in range.
            if nb_heroes != 0:
                #Computes how many xp each hero will get
                victory_points = monster_xp // nb_heroes
                if (monster_xp % nb_heroes) != 0:
                    victory_points += 1

                #Loop on heroes in range of monster to give them xp
                for hero in heroes_in_range:
                    data_base['heroes'][hero]['xp'] += victory_points

            #Set amount of xp given by monster to 0 when he got killed once.
            data_base['monsters'][monster]['xp'] = 0


def clear_board(data_base):
    """
    Check if a hero or a monster is dead to delete it from the board and display the board

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)

    """

    #Give xp and level up
    give_xp(data_base)
    level_up(data_base)

    #Refresh display
    display_board(data_base)


def display_endgame(data_base):
    """
    Display a message about who is the winner of the game

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)


    Version
    -------
    specification: Antoine Mouchet (v1 04/03/19)
                   Antoine Mouchet (v2 29/03/19)
    implementation: Antoine Mouchet (v1 30/03/19)

    """

    display = '-~-~-~-~-~-~-~-~-~-~-~-~-GAME OVER-~-~-~-~-~-~-~-~-~-~-~-~-\n\n\n'

    if data_base['color_win'] == '':
        display +='\t\t\tNOBODY WON THE GAME'
    
    elif data_base['color_win'] != '':
        display += '\t\t%s TEAM WON THE GAME' % data_base['color_win'].upper()

    display += '\n\n-~-~-~-~-~-~-~-~-~-~-~-~-~--~-~-~-~-~-~-~-~-~-~-~-~--~-~-~-'
    
    print(display)


# ACTIONS


def actions_monsters(data_base):
    """
    Choose actions of the monsters and return it

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)

    Returns
    -------
    monsters_actions: A sentence with name of the monsters and their moves (str)

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)

    """
    monsters_actions = ''

    #Loop on monsters
    for monster in data_base['monsters']:
        #Check if monster is alive
        if check_hp(data_base, monster, 'monsters'):

            #Get closest heroes in range of monster
            closest_heroes = get_closest_heroes(data_base, check_in_range_monster(monster, data_base), monster)
            
            #Check if there is more than one hero in range
            if len(closest_heroes) > 1:
                #get focus of monster
                hero_focused = get_focus(data_base, closest_heroes)

            #Only 1 hero in range
            elif len(closest_heroes) == 1:
                for hero in closest_heroes:
                    hero_focused = hero

            #Make sure that there is at least 1 hero in range
            if len(closest_heroes) != 0:

                #Check if monster is in range of attack
                if closest_heroes[hero_focused] < 2:
                    #Updates sentence of monsters
                    monsters_actions += '%s:*%d-%d ' % (monster, \
                    data_base['heroes'][hero_focused]['position'][0],\
                    data_base['heroes'][hero_focused]['position'][1])
                
                #Monster must move to reach hero
                else:
                    #Get best position to reach
                    monster_pos = get_direction(data_base, hero_focused, monster)
                    #Updates sentence of monsters
                    monsters_actions += '%s:@%d-%d ' % (monster, monster_pos[0], monster_pos[1])
    s.save_command(monsters_actions, 'monsters', data_base['nb_turns'])
    return monsters_actions


def get_focus(data_base, closest_heroes_in_range):
    """
    Returns the name of the hero to focus 

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    closest_heroes_in_range: dict of the closest heroes in range (dict)

    Returns
    -------
    hero_name: name of the hero to focus (str)

    Version
    -------
    specification: Antoine Mouchet (v1 30/03/19)
    implementation: Antoine Mouchet (v1 30/03/19)

    """
    
    # the hero to focus is the first of the list by default
    hero_name = ''
    
    for hero in closest_heroes_in_range:

        if hero_name == '':
            hero_name = hero

        #Checks if hero has less hp than previous focus
        elif data_base['heroes'][hero]['hp'] < data_base['heroes'][hero_name]['hp']:
            hero_name = hero

        #Checks if hero has less victory points than previous focus
        elif data_base['heroes'][hero]['xp'] < data_base['heroes'][hero_name]['xp']:
            hero_name = hero
 
        #Checks if hero's name is before in lexicographical order than its of previous focus
        elif hero.lower() < hero_name.lower():
            hero_name = hero

        #focus red team in priority
        elif data_base['heroes'][hero]['team'] == 'red' and data_base['heroes'][hero_name]['team'] == 'blue':
            hero_name = hero

    return hero_name


def get_direction(data_base, hero_name, monster_name):
    """
    Returns closest position of hero reachable by monster

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    hero_name: name of the closest hero (str)
    monster_name: name of the monster (str)

    Returns
    -------
    monster_pos: closest position of hero reachable by monster (list)

    Version
    -------
    specification: Antoine Mouchet (v1 30/03/19)
    implementation: Antoine Mouchet (v1 30/03/19)

    """
    #Monster position
    monster_row = data_base['monsters'][monster_name]['position'][0]
    monster_column = data_base['monsters'][monster_name]['position'][1]

    #hero position
    hero_row = data_base['heroes'][hero_name]['position'][0]
    hero_column = data_base['heroes'][hero_name]['position'][1]

    #Get best row to go to
    if (hero_row - monster_row) < 0:
        monster_row -= 1
    elif (hero_row - monster_row) > 0:
        monster_row += 1

    #Get best colum to go to
    if (hero_column - monster_column) < 0:
        monster_column -= 1
    elif (hero_column - monster_column) > 0:
        monster_column += 1
    
    return [monster_row, monster_column]


def get_closest_heroes(data_base, heroes_in_range, monster_name):
    """
    Returns a dico {'hero_name':distance_with_hero} of closest heroes of monster

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    heroes_in_range: list of heroes in range of monsters (list)
    monster_name: the name of the monster (str)

    Returns
    -------
    closest_heroes: dict of closest heroes with distance(dict)

    Version
    -------
    specification: Antoine Mouchet (v1 30/03/19)
    implementation: Antoine Mouchet (v1 30/03/19)

    """
    #Initialize dict of closest heroes and get row and column of monster
    closest_heroes = {}
    monster_row = data_base['monsters'][monster_name]['position'][0]
    monster_column = data_base['monsters'][monster_name]['position'][1]

    #Loop on heroes in list
    for hero in heroes_in_range:
    
        #computes distance with each hero in range
        distance = ((((data_base['heroes'][hero]['position'][0] - monster_row)**2+\
        (data_base['heroes'][hero]['position'][1] - monster_column)**2)**(.5)) // 1)

        #Check if there is already a hero who is as close or if there is no distance yet
        if len(closest_heroes) == 0:
            closest_heroes[hero] = distance

        for hero_name in heroes_in_range:
            if hero_name in closest_heroes:

                #Check if hero is as close as previous heroes
                if distance == closest_heroes[hero_name]:
                    closest_heroes[hero] = distance

                #Check if hero is closer than previous heroes
                elif distance < closest_heroes[hero_name]:
                    closest_heroes = {hero: distance}

    return closest_heroes
          

def check_in_range_monster(monster_name, data_base):
    """
    Returns a list of heroes in range of monster

    Parameters
    ----------
    monster_name: the name of the monster of which we are checking range (str)
    data_base: Dico with all informations about the game(dict)

    Return
    ------
    heroes_in_range: list of hero in range of monster (list)

    Version
    -------
    Specification: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 04/03/19)
                   Antoine Mouchet (V.2 18/03/19)
    Implementation: Antoine Mouchet (v1 18/03/19)

    """

    #Get position of monster
    e1_row = data_base['monsters'][monster_name]['position'][0]
    e1_column = data_base['monsters'][monster_name]['position'][1]

    #Initialize list of hero in range
    heroes_in_range = []

    for hero in data_base['heroes']:
        if check_hp(data_base, hero, 'heroes'):
            #Get position of hero
            e2_row = data_base['heroes'][hero]['position'][0]
            e2_column = data_base['heroes'][hero]['position'][1]

            #Computes distance between both entities
            distance = (((e2_row-e1_row)**2)+((e2_column-e1_column)**2))**(.5) // 1

            #Check if hero is in range of entity
            if distance <= data_base['monsters'][monster_name]['range']:
                #Add hero to the list of hero in range
                heroes_in_range.append(hero)

    return heroes_in_range


def check_in_range_hero(data_base, hero_name, target_type, target_name=None, case_coord=None, spell=None):
    """
    Returns True if target is in range of hero.

    Parameters
    -----------
    data_base: Dico with all informations about the game(dict)
    hero_name: name of the hero targetting someone (str)
    target_type: type of the target (str)
    target_name: name of the target (str)(optional)
    case_coord: coords of case targetted (list)(optional)
    spell: name of the spell used by hero (str)(optional)

    Returns
    -------
    in_range: True if target is in range (bool)

    Notes
    -----
    target_type must be heroes or monsters or case
    target_name must be specified if target_type is heroes or monsters
    case_coords must be specified if target_type is case
    Spell must be specified if hero is casting a spell otherwise
    The range of a hero is considered to be 1.

    Version
    -------
    Specification: Antoine Mouchet (v1 18/03/19)
    implementation: Antoine Mouchet (v1 19/03/19)

    """
    #Get coordinates of hero and target
    #HERO
    hero_row = data_base['heroes'][hero_name]['position'][0]
    hero_column = data_base['heroes'][hero_name]['position'][1]

   
    if target_type == 'monsters' or target_type == 'heroes':
        #TARGET
        target_row = data_base[target_type][target_name]['position'][0]
        target_column = data_base[target_type][target_name]['position'][1]

    elif target_type == 'case':
        target_row = case_coord[0]
        target_column = case_coord[1]

    #Computes distance between hero and target
    distance = (((target_row-hero_row)**2)+((target_column-hero_column)**2))**(.5) // 1

    #Check if a spell is used
    if spell is not None:
        #Get the range of the spell depending on hero level
        range_allowed = data_base['classes'][data_base['heroes'][hero_name]['class']][spell]['range'][data_base['heroes'][hero_name]['level']-1]

    else:
        #Sets range allowed to 1
        range_allowed = 1

    #Checks if target is in range of hero
    if distance <= range_allowed:
        return True

    return False


def actions_player(data_base, player_1, player_2, connection):
    """
    Ask to players heroes' actions, apply spells and return heroes_using_attack and heroes_using_move.

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    player_1: type of player 1 (str)
    player_2: type of player 2 (str)
    connection: sockets to receive/send orders (tuple)(optional)

    Notes
    -----
    player_1 and player_2 should be 'ia' or 'player' or 'away'

    Return
    ------
    heroes_using_attack: list with who's using the command attack and the coord. (list)
    heroes_using_move: list with who's using the command move and the coord. (list)

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19;V.2 28/03/19)
    Implementation: Simon Willame (V.1 28/03/19)

    """
    heroes_using_attack = [] #[['hero_name_1',[x,y]],...]
    heroes_using_move = []

    for team in ['red','blue']:
        #Check if both players are ia
        if player_1 == 'ia' and player_2 == 'ia':
            player_action = get_ia_actions(data_base, team)
        
        #Check if red player is an ia
        elif (player_1 == 'ia' and team == 'red') or (player_2 == 'ia' and team == 'blue'):
            player_action = get_ia_actions(data_base, team)

            #Check if other player is away
            if player_1 == 'away' or player_2 == 'away':
                mm.notify_remote_orders(connection, player_action)
        
        elif (player_1 == 'away' and team == 'red') or (player_2 == 'away' and team == 'blue'):
            player_action = mm.get_remote_orders(connection)

        #Both players are humans
        else:
            player_action = str(input('%s team, please write your heroes\' actions (Don\'t forget to write it: name_hero_1:action ...)\n' % team))

        s.save_command(player_action, team, data_base['nb_turns'])
        #Split heroes:action in a list
        
        player_action_first_split = player_action.split( )

        #Split heroes of their action
        player_action = []
        for hero_list in player_action_first_split:
            player_action.append(hero_list.split(':'))

        #manage action
        check_player=[]

        for action_player in player_action:    
            #check if hero already made an action and if hero exists in data_base
            if action_player[0] not in check_player and action_player[0] in data_base['heroes']:

                #check if the hero is in the right team and that hero is alive
                if data_base['heroes'][action_player[0]]['team'] == team and check_hp(data_base, action_player[0], 'heroes'):
                    check_player.append(action_player[0])
            
                    #command move (action_player[1] = '@x-y')
                    if '@' == action_player[1][0]:
                        coord = get_coord(action_player[1],'@')
                        if coord != []:
                            heroes_using_move.append([action_player[0], coord])

                    #command attack (action_player[1] = '*x-y')
                    elif '*' == action_player[1][0]:
                        coord = get_coord(action_player[1],'*')
                        if coord != []:
                            heroes_using_attack.append([action_player[0], coord])

                    #command spell
                    else:
                        cast_spell(data_base,action_player)

    return heroes_using_attack, heroes_using_move


def cast_spell(data_base, player_actions):
    """
    Cast spells

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    player_actions: list with information about who's using a spell, the name of the spell and the coord if needed (list)

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19, V.2 28/03/19)
    Implementation: Simon Willame (V.1 28/03/19)

    """
    #Checks that hero can cast spell
    if data_base['heroes'][player_actions[0]]['status'] != 'ovibus':
        #Spells with a target
        if player_actions[1] in ['fulgura', 'ovibus', 'reach', 'immunise']:

            #Convert coords from string to list
            coord = get_coord(player_actions[2])

            #get_coord return a blank list if the coord is bad written
            if coord !=[]:
                if player_actions[1] == 'fulgura':
                    fulgura(data_base, player_actions[0], coord)

                elif player_actions[1] == 'ovibus':
                    ovibus(data_base, player_actions[0], coord)

                elif player_actions[1] == 'reach':
                    reach(data_base, player_actions[0], coord)

                elif player_actions[1] == 'immunise':
                    immunise(data_base, player_actions[0], coord)

        #spell without target
        elif player_actions[1] == 'energise':
            energise(data_base, player_actions[0])

        elif player_actions[1] == 'stun':
            stun(data_base, player_actions[0])

        elif player_actions[1] == 'invigorate':
            invigorate(data_base, player_actions[0])

        elif player_actions[1] == 'burst':
            burst(data_base, player_actions[0])


def get_coord(coord, avoid_character=None):
    """
    Return a list of int.

    Parameter
    ---------
    coord: a string with the coord. (str)
    avoid_character: a string with the character to avoid in coord. (str)
    
    Return
    ------
    a_coord: a list with 2 int, first means X and the second means Y. (list)

    Note
    ----
    If coord isn't well written, get_coord returns a blank list.

    Version
    -------
    Specification: Simon Willame (V.1 28/03/19)
    Implementation: Simon Willame (V.1 28/03/19)

    """
    a_coord= []
    
    if coord.count('-') == 1:
        if avoid_character != None:
            coord = coord[1:].split('-')
        else:
            coord = coord.split('-')

        #check if there only a X and an Y and they aren't character
        if len(coord) == 2:
            #check AFTER to avoid any bug 
            if coord[0].isdigit() and coord[1].isdigit():
                #loop on coord to add it
                for x in coord:
                        a_coord.append(int(x))


    return a_coord


def check_hp_max(data_base, hero_name):
    """
    Sets hp to hp max allowed by level if hp are above hp max

    Parameters
    ----------
    data_base: dico with all informations about the game(dict)
    hero_name: the name of the hero to check hp from (str)

    Version
    -------
    Specification: Blandine Willemart, Antoine Mouchet (v2 08/03/19)
    implementation: Antoine Mouchet (v1 26/03/19)

    """
    #Get maximum of hp allowed by level and class of hero
    hp_max_allowed = data_base['classes'][data_base['heroes'][hero_name]['class']]['hp_max'][data_base['heroes'][hero_name]['level']-1]

    if data_base['heroes'][hero_name]['hp'] > hp_max_allowed:
        #Sets hp to maximum allowed if actual hp too high
        data_base['heroes'][hero_name]['hp'] = hp_max_allowed


def check_case_occupied(data_base, position_asked):
    """
    Return True if case is occupied.

    Parameters
    ----------
    data_base: dico with all informations about the game(dict)
    position_asked: position where hero wants to move (list)

    Returns
    -------
    case_occupied: True if there is someone on the case (bool)

    Version
    -------
    Specification: Blandine Willermart (v1 04/03/19)
    Implementation: Antoine Mouchet (v1 25/03/19)

    """
    #Loop on heroes and monsters
    for entity_type in ['monsters', 'heroes']:
        for entity in data_base[entity_type]:
    
            #Check if position asked is already occupied by an entity.
            #And if entity is alive
            if data_base[entity_type][entity]['position'] == position_asked\
            and check_hp(data_base, entity, entity_type):
        
                return True

    return False


def respawn(data_base):
    """
    Resets hp and stats of heroes to the max allowed by their level.

    Parameters
    ----------
    data_base: dico with all informations about the game(dict)

    Version
    -------
    Specification: Blandine Willemart (v1 04/03/19)
    Implementation: Antoine Mouchet (v1 18/03/19)

    """
    
    #Loop on hero
    for hero_name in data_base['heroes']:

        #Get informations about the hero
        hero_class = data_base['heroes'][hero_name]['class']
        hero_level = data_base['heroes'][hero_name]['level']

        #Checks if hero is dead
        if data_base['heroes'][hero_name]['hp'] <= 0:
            #Reset health points of hero
            data_base['heroes'][hero_name]['hp'] = data_base['classes'][hero_class]['hp_max'][hero_level-1]
            #Reset position of hero
            data_base['heroes'][hero_name]['position'] = data_base['spawns'][data_base['heroes'][hero_name]['team']]
        
        #Decrease number turns left of status of hero
        if data_base['heroes'][hero_name]['status_turn'] != 0:
            data_base['heroes'][hero_name]['status_turn'] -= 1

        #Checks if hero has a special status (means that status_turn is at 0) and reset it if it's the case
        elif data_base['heroes'][hero_name]['status'] != 'neutral':
            data_base['heroes'][hero_name]['status'] = 'neutral'

        #Reset bonus of hero
        data_base['heroes'][hero_name]['bonus'] = 0

        #Reduce cooldown of spell by 1 if spell in cooldown.
        if data_base['heroes'][hero_name]['cooldown1'] > 0:
            data_base['heroes'][hero_name]['cooldown1'] -= 1
        if data_base['heroes'][hero_name]['cooldown2'] > 0:
            data_base['heroes'][hero_name]['cooldown2'] -= 1


def basic_attack(data_base, attack_command_hero=[], attack_command_monster=[]):
    """
    Attacks the entity on case inserted with the hero attacking and the target position

    Parameters
    ----------
    data_base: dico with all informations about the game(dict)
    attack_command_hero : list with the heroes who want to attack. (list)
    attack_command_monster : list with the monsters who want to attack. (list)

    Note
    ----
    attack_commmand_hero and attack_command_monster are blank list if noboby is attacking

    Version
    -------
    specification: Blandine Willemart (v1 04/03/19)
                   Simon Willame (V.2 31/03/19)
    Implementation: Simon Willame (V.1 31/03/19)
    """
    #attack_command is supposed to be like: [ [ hero_name, [x,y] ],...]

    #Loop on monster's attack
    for attacking_monster in attack_command_monster:
        #check if monster can attack
        if data_base['monsters'][attacking_monster[0]]['status'] != 'ovibus':

            #Loop on heroes
            for hero in data_base['heroes']:

                    #Check if hero is on the case
                    if data_base['heroes'][hero]['position'] == attacking_monster[1]:

                        #Check hero is not immunised
                        if data_base['heroes'][hero]['status'] != 'immunise':

                            #Get monster's damage
                            damage_dealt = data_base['monsters'][attacking_monster[0]]['damage'] + data_base['monsters'][attacking_monster[0]]['bonus']
                            #Rule: if damages are lower than 1, set them on 1
                            if damage_dealt < 1:
                                damage_dealt = 1
        
                            data_base['heroes'][hero]['hp'] -= damage_dealt
                            data_base['damage_dealed'] = True

    #Loop on hero attacking
    for attacking_hero in attack_command_hero:
        #Check if hero can attack
        if data_base['heroes'][attacking_hero[0]]['status'] != 'ovibus':
            #Get hero damage( basic damage + bonus)
            damage_dealt = data_base['classes'][data_base['heroes'][attacking_hero[0]]['class']]['damage'][data_base['heroes'][attacking_hero[0]]['level']-1] + data_base['heroes'][attacking_hero[0]]['bonus']
            if damage_dealt < 1 :
                damage_dealt = 1
            #Check if hero is attacking someone
            if check_case_occupied(data_base, attacking_hero[1]) == True:
                
                #Loop on monsters
                for monster in data_base['monsters']:
                    #check if monster is on the case
                    #and it is in range to be attacked
                    if data_base['monsters'][monster]['position'] == attacking_hero[1]\
                    and check_in_range_hero(data_base, attacking_hero[0], 'monsters', monster):

                            #Reduce monster's hp
                            data_base['monsters'][monster]['hp'] -= damage_dealt
                            data_base['damage_dealed'] = True

                #Loop on hero
                for hero in data_base['heroes']:

                    #check if hero is on the case
                    #and he is on range to be attacked
                    if data_base['heroes'][hero]['position'] == attacking_hero[1]\
                    and check_in_range_hero(data_base, attacking_hero[0], 'heroes', hero):
            
                        # check invicibility
                        # and friendly fire

                        if data_base['heroes'][hero]['status'] != 'immunise'\
                        and data_base['heroes'][attacking_hero[0]]['team'] != data_base['heroes'][hero]['team']:

                            #Reduce hero's hp
                            data_base['heroes'][hero]['hp'] -= damage_dealt
                            data_base['damage_dealed'] = True


def movements(data_base, move_command_hero=[], move_command_monster=[]):
    """
    Changes position of hero and monster based on command of player

    Parameters
    ----------
    data_base: dico with all informations about the game(dict)
    move_command_hero: list with heroes' names and and their coord (list)(optional)
    move_command_monster: list with names of the monsters and their coord (list)(optional)

    Note
    ----
    This function calls check_case_occupied to make sure
    nothing is on case before moving hero.
    move_command_hero and move_command_monster are set on a blank list if no one is moving

    Version
    -------
    Specification: Blandine Willermart (v1 04/03/19)
                   Simon Willame, Blandine Willemart (V.2 02/04/19)
    Implementation: Simon Willame (V.1 02/04/19)
    """
    #moving monster
    #Loop on movements command for monsters
    for movement in move_command_monster:
        #Check monster exists,  that case reached is not occupied by someone else and isn't out of range of the map 
        if movements_condition(data_base, 'monsters', movement):
            #change monster's position
            data_base['monsters'][movement[0]]['position'] = movement[1]

    #moving hero
    #Loop on movements command for heroes
    for movement in move_command_hero:

        #Check hero exists, that case reached is not occupied by someone else and isn't out of range of map
        #and that case is in range
        if movements_condition(data_base, 'heroes', movement) and check_in_range_hero(data_base, movement[0], 'case', case_coord=movement[1]):

            #Change hero's position
            data_base['heroes'][movement[0]]['position'] = movement[1]


def movements_condition(data_base, entity_type, movement):
    """
    Return True if all the usual conditions to move are correct, False otherwise.

    Parameters
    ----------
    data_base: dico with all informations about the game(dict)
    entity_type: the type of entity who is playing. Heroes or Monster (str)
    movement: list with the name of the entity and their coord (list)

    Returns
    -------
    True if all the conditions to move are correct, False otherwise

    Version
    -------
    Specification: Simon Willame (V.1 06/04/19)
    Implementation: Simon Willame (V.1 06/04/19)
    
    """
    # Conditions are : - entity exist -the case if free - case isn't out of range -entity isn't 'ovibus'
    if movement[0] in data_base[entity_type] and not check_case_occupied(data_base, movement[1]) and check_case_in_board(data_base, movement[1]):
	#Check player is not moving on hill before turn 20.
        if movement[1] in data_base['hill'] and data_base['nb_turns'] < 20:
            return False

        if data_base[entity_type][movement[0]]['status'] != 'ovibus':
            return True

    return False


def clear_monster_command_sentence(data_base, monsters_actions):
    """
    Return two list: monster_attacking and monster_moving.
    
    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    monsters_actions: A sentence with name of the monsters and their moves (str)
    
    Return
    ------
    monster_attacking: a list with name of the attacking monsters and their target coord (list)
    monster_moving: a list with name of the moving monsters and their new coord (list)
    Version
    -------
    Specification: Simon Willame (V.1 02/04/19)
    Implementation: Simon Willame (V.1 02/04/19)
    """
    #monsters_actions_first_split = ['monster_name:*x-y or @x-y']
    monsters_actions_first_split = monsters_actions.split( )
    uncleared_monsters_action = []
    for monster in monsters_actions_first_split:
        #uncleared_monsters_action = [['monster_name']['*x-y or @x-y']]
        uncleared_monsters_action.append(monster.split(':'))
    
    #Initialize lists
    monster_attacking = []
    monster_moving = []
    check_monster = []
    #Get spawns
    spawns = []
    for color_team in data_base['spawns']:
        spawns.append(data_base['spawns'][color_team]) 

    #Loop on actions of monster
    for action_monster in uncleared_monsters_action:
        if action_monster[0] not in check_monster and action_monster[0] in data_base['monsters']:
            check_monster.append(action_monster[0])
            #command move
            if '@' in action_monster[1][0]:
                coord = get_coord(action_monster[1],'@')
                #Check monster is not moving on spawn
                if coord not in spawns:
                    monster_moving.append([action_monster[0], coord])

            #command attack
            elif '*' in action_monster[1][0]:
                coord = get_coord(action_monster[1],'*')
                #Check monster is not attacking spawn
                if coord not in spawns:
                    monster_attacking.append([action_monster[0], coord])

    return monster_attacking, monster_moving


def check_case_in_board(data_base, case):
    """
    Returns True if case is inside board

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    case: case we're checking (list)

    Returns
    -------
    in_board: True if case inside the board (bool)

    Version
    -------
    specification: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 05/04/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 05/04/19)
    """
    if case[0] <= 0 or case[1] > data_base['board'][1] or\
     case[0] > data_base['board'][0] or case[1] <= 0:
        return False

    return True


def ia_actions(data_base, ia_team):
    """
    Returns actions of naive ia

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    ia_team: color of the team of ia (str)

    Returns
    -------
    ia_action: sentence with all actions of ia (str)

    Version
    --------
    specification: Antoine Mouchet (v1 05/04/19)
    implementation: Antoine Mouchet (v1 05/04/19)

    """
    ia_action = ''

    #Loop on hero
    for hero in data_base['heroes']:

        #Check ia is using only its heroes
        if data_base['heroes'][hero]['team'] == ia_team:

            #Get random action and row and column of hero
            random_action = random.randint(0,2)
            row = random.randint(data_base['heroes'][hero]['position'][0]-1, data_base['heroes'][hero]['position'][0]+1)
            column = random.randint(data_base['heroes'][hero]['position'][1]-1, data_base['heroes'][hero]['position'][1]+1)
    
            #Deplacement
            if random_action == 0:
                ia_action += '%s:@%d-%d ' % (hero, row, column)
            
            #Attack
            elif random_action == 1:
                ia_action += '%s:*%d-%d ' % (hero, row, column)
            
            #Spell
            elif random_action == 2:
                #Get random spell
                list_spell = ['energise', 'fulgura', 'immunise', 'reach', 'burst', 'stun', 'invigorate', 'ovibus']
                spell_id = random.randint(0, len(list_spell)-1)
                spell = list_spell[spell_id]

                #Check if spell needs target
                if spell in ['immunise', 'reach', 'fulgura', 'ovibus']:
                    ia_action += '%s:%s:%d-%d ' % (hero, spell, row, column)
                else:
                    ia_action += '%s:%s ' % (hero, spell)

    return ia_action


def level_up(data_base):
    """
    Make hero level up if enough xp

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)

    Version
    -------
    specification: Antoine Mouchet (v1 06/04/19)
    implementation: Antoine Mouchet (v1 06/04/19)
    
    """
    #Loop on hero
    for hero_name in data_base['heroes']:
        #Get xp and previous level of hero
        hero_xp = data_base['heroes'][hero_name]['xp']
        hero_level = data_base['heroes'][hero_name]['level']

        #Level up if enough victory points
        if hero_xp >= 100 and hero_xp < 200:
            data_base['heroes'][hero_name]['level'] = 2
        elif hero_xp >= 200 and hero_xp < 400:
            data_base['heroes'][hero_name]['level'] = 3
        elif hero_xp >= 400 and hero_xp < 800:
            data_base['heroes'][hero_name]['level'] = 4
        elif hero_xp >= 800:
            data_base['heroes'][hero_name]['level'] = 5

        #Check if hero levelled up
        if hero_level < data_base['heroes'][hero_name]['level']:
            data_base['heroes'][hero_name]['hp'] = data_base['classes'][data_base['heroes'][hero_name]['class']]['hp_max'][data_base['heroes'][hero_name]['level']-1]


def check_hill(data_base):
    """
    Updates the color of winning team

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)

    Version
    --------
    Specification: Willemart Blandine (V.1 08/04/19)
    Implementation: Willemart Blandine (V.1 09/04/19)

    """
    #Initialize variables
    previous_color = data_base['color_win']
    colors_on_hill = []

    #Loop on heroes
    for hero in data_base['heroes']:
        #Check if hero is on hill
        #Add his color to the list of colors if yes
        if data_base['heroes'][hero]['position'] in data_base['hill']:
            colors_on_hill.append(data_base['heroes'][hero]['team'])
    
    #Nobody on hill
    if len(colors_on_hill) == 0:
        data_base['nb_turns_on_hill'] = 0
        data_base['color_win'] = ''
    
    #One hero on hill or all heroes on the same team
    elif len(colors_on_hill) == 1 or only_color(colors_on_hill):

        #Same team than before
        if colors_on_hill[0] == previous_color:
            data_base['nb_turns_on_hill'] += 1

        #Different team
        else:
            data_base['nb_turns_on_hill'] = 1
            data_base['color_win'] = colors_on_hill[0]

    else:
        data_base['nb_turns_on_hill'] = 0
        data_base['color_win'] = ''


def only_color(color_list, previous_color='', is_only=True):
    """
    Returns True if all items of list are the same

    Parameters
    ----------
    color_list: list of items (list)
    previous_color: the previous item of the list (optional)(str)
    is_only: memory variable of veracity (optional)(bool)

    Return
    ------
    is_only: True if all elements are the same (bool)

    Version
    --------
    Specification: Willemart Blandine (V.1 08/04/19)
    Implementation: Willemart Blandine (V.1 09/04/19)

    """
    #First item of the list is set-up as base
    if previous_color == '':
        return only_color(color_list[1:], color_list[0], True)
    
    #No item to test left, return result
    if len(color_list) == 0:
        return is_only

    #Check if item is different from previous item
    #Return false if it's the case
    elif color_list[0] != previous_color:
        return False

    #Test next item
    else:
        return only_color(color_list[1:], previous_color)


def end_turn(data_base):
    """
    Function marking the end of a turn, miscellaneous actions on monsters and heroes

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)

    Version
    -------
    specification: Antoine Mouchet (v1 06/04/19)
    implementation: Antoine Mouchet (v1 06/04/19)

    """
    #Loop on monsters
    for monster in data_base['monsters']:
        #Reset bonus of monster
        data_base['monsters'][monster]['bonus'] = 0

        #Decrease number turns left of status of monster
        if data_base['monsters'][monster]['status_turn'] != 0:
            data_base['monsters'][monster]['status_turn'] -= 1

        #Checks if monster has a special status (means that status_turn is at 0) and reset it if it's the case
        elif data_base['monsters'][monster]['status'] != 'neutral':
            data_base['monsters'][monster]['status'] = 'neutral'
    
    #give xp and level up
    give_xp(data_base)
    level_up(data_base)

    #Respawn dead heroes
    respawn(data_base)

    #If turn 20 then check if someone is on hill
    if data_base['nb_turns'] >= 20:
        check_hill(data_base)
    
    #Increase number of turn by 1
    data_base['nb_turns'] += 1

    #Check if damage were dealed during the turn
    #Updates number of turns afk
    if data_base['damage_dealed'] == True:
        data_base['nb_turns_afk'] = 0
    else:
        data_base['nb_turns_afk'] += 1

    #Resets damage dealed info for next turn
    data_base['damage_dealed'] = False


# SPELLS


def energise(data_base, hero_name):
    """
    Add x damage point for allied heroes in range  

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: name of hero casting the spell (str)

    Note
    ----
    it's a barbarian spell

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet (v1 19/03/19)

    """
    #Get level of hero
    hero_level = data_base['heroes'][hero_name]['level']

    #Checks if hero has minimum level to cast the spell
    if hero_level < 2:
        print('Energise can not be used because %s is not level 2.' % hero_name)
    
    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown1'] != 0:
        print('Energise is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown1'])

    #Checks that hero is a barbarian.
    elif data_base['heroes'][hero_name]['class'] == 'barbarian' :

        #Loop on heroes in data base
        for hero in data_base['heroes']:
    
            #Check if heroes are in the same team
            #and if hero is in the range
            #and that hero is not casting on himself
            if data_base['heroes'][hero]['team'] == data_base['heroes'][hero_name]['team'] \
            and check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='energise')\
            and hero != hero_name:
    
                #Update bonus of targets
                data_base['heroes'][hero]['bonus'] += data_base['classes']['barbarian']['energise']['ratio'][hero_level-1]

        #Update cooldown of spell
        data_base['heroes'][hero_name]['cooldown1'] = data_base['classes']['barbarian']['energise']['cooldown'][hero_level-1] + 1


def stun(data_base, hero_name):
    """
    Reduce damage of the monsters or ennemi heroes of x point.

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: the name of the hero casting spell

    Note
    ----
    character's damage can't be lower than 1
    it's a barbarian spell

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
                   Simon Willame, Blandine Willemart (v2 26/03/19)
    Implémentation: Blandine Willemart (v.1 26/03/19)
    """
    #Get level of hero and damage of spell
    hero_level = data_base['heroes'][hero_name]['level']
    spell_damage = data_base['classes']['barbarian']['stun']['ratio'][hero_level-1]

    #Checks if hero has a level high enough to cast stun
    if hero_level < 3:
        print('Stun can not be casted because %s is not level 3.' % hero_name)
    
    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown2'] != 0:
        print('Stun is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown2'])

    #Checks that hero is a barbarian
    elif data_base['heroes'][hero_name]['class'] == 'barbarian':

        #Loop on heroes in data base
        for hero in data_base['heroes']:
    
            #Check if heroes aren't in the same team
            #and if hero is in the range
            #and that hero is not casting on himself
            if data_base['heroes'][hero]['team'] != data_base['heroes'][hero_name]['team'] \
            and check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='stun')\
            and hero != hero_name:
    
                #Update bonus of targets
                data_base['heroes'][hero]['bonus'] -= spell_damage
                
        #Loop on monsters in data base
        for monster in data_base['monsters']:
    
            #Check if monster is in the range
            if check_in_range_hero(data_base, hero_name, 'monsters', monster, spell='stun'):
    
                #Update bonus of targets
                data_base['monsters'][monster]['bonus'] -= spell_damage

        #Update cooldown of spell
        data_base['heroes'][hero_name]['cooldown2'] = data_base['classes']['barbarian']['stun']['cooldown'][hero_level-1] + 1


def invigorate(data_base, hero_name):
    """
    Add x for allied heroes' health point in range

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: the name of the hero (str)

    Note
    -----
    it's an healer spell
    Health point can't be higher than maximum health

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet (v1 29/03/19)

    """
    #Get level of hero
    hero_level = data_base['heroes'][hero_name]['level']

    #Checks if hero has minimum level to cast the spell
    if hero_level < 2:
        print('Invigorate can not be used because %s is not level 2.' % hero_name)

    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown1'] != 0:
        print('Invigorate is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown1'])

    #Checks that hero is a healer
    elif data_base['heroes'][hero_name]['class'] == 'healer':

        #Loop on heroes in data base
        for hero in data_base['heroes']:
    
            #Check if heroes are in the same team and if hero is in the range and that hero is not casting on himself
            if data_base['heroes'][hero]['team'] == data_base['heroes'][hero_name]['team'] \
                and check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='invigorate') and hero != hero_name:
    
                #Update hps of targets
                data_base['heroes'][hero]['hp'] += data_base['classes']['healer']['invigorate']['ratio'][hero_level-1]
                check_hp_max(data_base, hero)

        #Update cooldown of spell
        data_base['heroes'][hero_name]['cooldown1'] = data_base['classes']['healer']['invigorate']['cooldown'][hero_level-1] + 1


def immunise(data_base, hero_name, target):
    """
    Give invicibility to an allied hero during 1 turn.

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: name of hero casting the spell (str)
    target: position targetted by spell (list)

    Note
    ----
    it's an healer spell
    Invicibility protect his owner from all kind of damage exepct Fulgura or Burst

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)

    """
    #Get level of hero
    hero_level = data_base['heroes'][hero_name]['level']

    #Checks if hero has minimum level to cast the spell
    if hero_level < 3:
        print('Immunise can not be used because %s is not level 3.' % hero_name)

    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown2'] != 0:
        print('Immunise is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown2'])

    elif data_base['heroes'][hero_name]['class'] == 'healer':
        #Loop on heroes
        for hero in data_base['heroes']:

            #Check if hero is the target
            if data_base['heroes'][hero]['position'] == target:

                #Check if target in range
                #Check that heroes are in the same team
                #Check hero isn't casting on himself
                if check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='immunise') and \
                    data_base['heroes'][hero_name]['team'] == data_base['heroes'][hero_name]['team'] and \
                    hero != hero_name:

                    #Update status and status turn
                    data_base['heroes'][hero]['status'] = 'immunise'
                    data_base['heroes'][hero]['status_turn'] = 1

        #Update cooldown
        data_base['heroes'][hero_name]['cooldown2'] = data_base['classes']['healer']['immunise']['cooldown'][hero_level-1] + 1


def fulgura(data_base, hero_name, target):
    """
    Reduce target's healt point of x points

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: name of hero casting spell (str)
    target: case targetted (list)

    Note
    -----
    It's a mage spell

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)

    """
    #Get level of hero and damage of spell
    hero_level = data_base['heroes'][hero_name]['level']
    spell_damage = data_base['classes']['mage']['fulgura']['ratio'][hero_level -1]

    #Checks if hero has minimum level to cast the spell
    if hero_level < 2:
        print('Fulgura can not be used because %s is not level 2.' % hero_name)

    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown1'] != 0:
        print('Fulgura is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown1'])

    elif data_base['heroes'][hero_name]['class'] == 'mage':
        for hero in data_base['heroes']:

            #Check if hero is the target
            if data_base['heroes'][hero]['position'] == target:

                #Check if target is in range, that target is not in the same team
                if check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='fulgura') and \
                    data_base['heroes'][hero_name]['team'] != data_base['heroes'][hero_name]['team'] and \
                    hero != hero_name:

                    data_base['heroes'][hero]['hp'] -= spell_damage
                    data_base['damage_dealed'] = True

        #Loop on monsters
        for monster in data_base['monsters']:
            #Check if monster is the target
            if data_base['monsters'][monster]['position'] == target:
                #Check if monster is in range
                if check_in_range_hero(data_base, hero_name, 'monsters', monster, spell='fulgura'):
                    data_base['monsters'][monster]['hp'] -= spell_damage
                    data_base['damage_dealed'] = True

        #Sets cooldown
        data_base['heroes'][hero_name]['cooldown1'] = data_base['classes']['mage']['fulgura']['cooldown'][hero_level-1] + 1


def ovibus(data_base, hero_name, target):
    """
    Remove action of monster or ennemi hero during 1 turn.

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: name of hero casting the spell (str)
    target: case targetted by spell (list)

    Note
    -----
    It's a mage spell

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)

    """

    #Get level of hero
    hero_level = data_base['heroes'][hero_name]['level']

    #Checks if hero has minimum level to cast the spell
    if hero_level < 3:
        print('Ovibus can not be used because %s is not level 3.' % hero_name)

    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown2'] != 0:
        print('Ovibus is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown2'])

    elif data_base['heroes'][hero_name]['class'] == 'mage':
        #Loop on hero
        for hero in data_base['heroes']:
            #Checks if hero is targetted
            if data_base['heroes'][hero]['position'] == target:
            
                #Check if hero is in range, if target is not in the same team and
                if check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='ovibus') and \
                    data_base['heroes'][hero_name]['team'] != data_base['heroes'][hero_name]['team'] and \
                    hero != hero_name:
                    data_base['heroes'][hero]['status'] = 'ovibus'
                    data_base['heroes'][hero]['status_turn'] = data_base['classes']['mage']['ovibus']['ratio'][hero_level - 1] + 1
    
        #Loop on monsters
        for monster in data_base['monsters']:
            #Checks if monster is the target
            if data_base['monsters'][monster]['position'] == target:

                #Checks if monster is in range
                if check_in_range_hero(data_base, hero_name, 'monsters', monster, spell='ovibus'):
                    data_base['monsters'][monster]['status'] = 'ovibus'
                    data_base['monsters'][monster]['status_turn'] = data_base['classes']['mage']['ovibus']['ratio'][hero_level - 1] + 1

        data_base['heroes'][hero_name]['cooldown2'] = data_base['classes']['mage']['ovibus']['cooldown'][hero_level-1] + 1
    

def burst(data_base, hero_name):
    """
    Reduce x Health point of ennemi around the Rogue

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: Name of the hero casting the spell (str)

    Note
    ----
    It's a rogue spell

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)

    """
    #Get level of hero and damage of spell
    hero_level = data_base['heroes'][hero_name]['level']
    spell_damage = data_base['classes']['rogue']['burst']['ratio'][hero_level-1]

    #Checks if hero has a level high enough to cast burst
    if hero_level < 3:
        print('Burst can not be casted because %s is not level 3.' % hero_name)
    
    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown2'] != 0:
        print('Burst is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown2'])

    #Checks that hero is a rogue.
    elif data_base['heroes'][hero_name]['class'] == 'rogue':

        #Loop on heroes in data base
        for hero in data_base['heroes']:
    
            #Check if heroes aren't in the same team and if hero is in the range and that hero is not casting on himself
            if data_base['heroes'][hero]['team'] != data_base['heroes'][hero_name]['team'] \
                and check_in_range_hero(data_base, hero_name, 'heroes', hero, spell='burst') and hero != hero_name:
    
                #Update bonus of targets
                data_base['heroes'][hero]['hp'] -= spell_damage
                data_base['damage_dealed'] = True
                
        #Loop on monsters in data base
        for monster in data_base['monsters']:
    
            #Check if monster is in the range
            if check_in_range_hero(data_base, hero_name, 'monsters', monster, spell='burst'):
    
                #Update bonus of targets
                data_base['monsters'][monster]['hp'] -= spell_damage
                data_base['damage_dealed'] = True

        #Update cooldown of spell
        data_base['heroes'][hero_name]['cooldown2'] = data_base['classes']['rogue']['burst']['cooldown'][hero_level-1] + 1


def reach(data_base, hero_name, target):
    """
    Put hero on a chosen position (x,y)

    Parameters
    ----------
    data_base: Dico with all informations about the game(dict)
    hero_name: Name of hero casting the spell (str)
    target: case to reach (list)

    Note
    ----
    It's a rogue spell
    Rogue can't teleport if someone wants to teleport on the same position
    or if someone is on the position

    Version
    -------
    Specification: Simon Willame (V.1 02/03/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 29/03/19)
    """
    #Get level of hero
    hero_level = data_base['heroes'][hero_name]['level']

    #Checks if hero has minimum level to cast the spell
    if hero_level < 2:
        print('Reach can not be used because %s is not level 2.' % hero_name)

    #Checks spell is not in cooldown
    elif data_base['heroes'][hero_name]['cooldown1'] != 0:
        print('Reach is in cooldown: %d turns left.' % data_base['heroes'][hero_name]['cooldown2'])

    #Checks hero is a rogue
    elif data_base['heroes'][hero_name]['class'] != 'rogue':
        print('%s is not a rogue.' % hero_name)
    
    elif not check_case_occupied(data_base, target) and check_in_range_hero(data_base, hero_name, 'case', case_coord=target, spell='reach'):

        data_base['heroes'][hero_name]['position'] = target
        data_base['heroes'][hero_name]['cooldown1'] = data_base['classes']['rogue']['reach']['cooldown'][hero_level-1] + 1


##IA

def get_closest_monster(data_base, hero_name):
    """
    Returns a dico {'hero_name':distance_with_hero} of closest monsters of hero

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    hero_name: the name of the hero (str)

    Returns
    -------
    closest_monsters: dict of closest monsters with distance(dict)

    Version
    -------
    specification: Antoine Mouchet (v1 30/03/19)
    implementation: Antoine Mouchet (v1 30/03/19)

    """
    #Initialize dict of closest monsters, distance with monsters and smallest_distance existing
    distance_monsters = {}
    closest_monsters = {}
    smallest_distance = 0

    #Get row and column of hero    
    hero_row = data_base['heroes'][hero_name]['position'][0]
    hero_column = data_base['heroes'][hero_name]['position'][1]

    #Loop on monsters in dict
    for monster in data_base['monsters']:

        #Check monster is alive
        if check_hp(data_base, monster, 'monsters'):

            #computes distance with each monster in range
            distance = ((((data_base['monsters'][monster]['position'][0] - hero_row)**2+\
            (data_base['monsters'][monster]['position'][1] - hero_column)**2)**(.5)) // 1)

            #Add distance to dict
            distance_monsters[monster] = distance

    for monster_name in distance_monsters:
        #Check if dict of closest monsters is empty
        if len(closest_monsters) == 0:
            closest_monsters[monster_name] = distance_monsters[monster_name]
            smallest_distance = distance_monsters[monster_name]
    
        #Check if monster is as far as previous one
        elif smallest_distance == distance_monsters[monster_name]:  
            closest_monsters[monster_name] = smallest_distance

        #Check if monster is closer than previous monsters
        elif smallest_distance > distance_monsters[monster_name]:

            #Restart dictionary with new smallest value
            closest_monsters = {monster_name: distance_monsters[monster_name]}
            #Define new smallest distance
            smallest_distance = distance_monsters[monster_name]

    return closest_monsters


def get_focus_monster(data_base, closest_monsters):
    """
    Returns the name of the monster to focus 

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    closest_monsters: dict of the closest monsters (dict)

    Returns
    -------
    monster_name: name of the monster to focus (str)

    Version
    -------
    specification: Antoine Mouchet (v1 30/03/19)
    implementation: Antoine Mouchet (v1 30/03/19)

    """
    
    # the monster to focus is the first of the list by default
    monster_name = ''
    
    for monster in closest_monsters:

        if monster_name == '':
            monster_name = monster

        #Checks if hero gives more xp than previous focus
        elif data_base['monsters'][monster]['xp'] > data_base['monsters'][monster_name]['xp']:
            monster_name = monster

        #Checks if monster has less damage points than previous focus
        elif data_base['monsters'][monster]['damage'] < data_base['monsters'][monster_name]['damage']:
            monster_name = monster

        #Checks if monster has less health points than previous focus
        elif data_base['monsters'][monster]['hp'] < data_base['monsters'][monster_name]['hp']:
            monster_name = monster

        #Checks if monster's name is before in lexicographical order than its of previous focus
        elif monster.lower() < monster_name.lower():
            monster_name = monster

    return monster_name


def get_direction_entity(data_base, hero_name, entity_type, entity_name=None, case_coords=None):
    """
    Returns closest position of entity reachable by hero

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    hero_name: name of the closest hero (str)
    entity_type: type of the entity to reach (str)
    entity_name: name of the entity to reach (str)(optional)
    case_coords: coords of case to reach (list)(optional)

    Notes
    -----
    entity_type can be 'heroes', 'monsters' or 'case'
    when entity_type = 'heroes' or 'monsters', entity_name must be specified
    otherwise case_coords should be specified

    Returns
    -------
    hero_pos: closest position of entity reachable by hero (list)

    Version
    -------
    specification:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)
    implementation:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)

    """
    #Check if entity to reach is monsters or heroes
    if entity_type != 'case':
        entity_row = data_base[entity_type][entity_name]['position'][0]
        entity_column = data_base[entity_type][entity_name]['position'][1]
    
    #Check if entity is a case
    else:
        entity_row = case_coords[0]
        entity_column = case_coords[1]

    #hero position
    hero_row = data_base['heroes'][hero_name]['position'][0]
    hero_column = data_base['heroes'][hero_name]['position'][1]


    #Get best row to go to
    vertical = ''
    #Go up
    if (hero_row - entity_row) < 0:
        hero_row += 1
        vertical = 'up'
    #Go down
    elif (hero_row - entity_row) > 0:
        hero_row -= 1
        vertical = 'down'

    #Get best colum to go to
    horizontal = ''
    #Go right
    if (hero_column - entity_column) < 0:
        hero_column += 1
        horizontal = 'right'
    #Go left
    elif (hero_column - entity_column) > 0:
        hero_column -= 1
        horizontal = 'left'
    
    #Check if case to reach is busy
    if check_case_occupied(data_base, [hero_row, hero_column]):
        
        #to avoid being blocked, modify position to reach
        #Vertical movements
        if vertical == 'up':
            if horizontal == 'right':
                hero_column -= 1
            elif horizontal == 'left' or horizontal == '':
                hero_column += 1

    
        elif vertical == 'down':
            if horizontal == 'right':
                hero_column -= 1
            elif  horizontal == 'left' or horizontal == '':
                hero_column += 1

        
        #Horizontal movements
        elif vertical == '':
            if horizontal == 'right' or 'left':
                hero_row += 1


    return [hero_row, hero_column]


def get_xp_available(data_base):
    """
    Returns total amount of xp available

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)

    Returns
    -------
    xp_available: the sum of xp available (float)

    Version
    -------
    specification:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)
    implementation:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)

    """
    xp_available = 0

    #Loop on monsters
    for monster_name in data_base['monsters']:
        #Check if monster is alive
        if data_base['monsters'][monster_name]['hp'] > 0:
            #Add monster's victory point to total amount of xp available.
            #Divided by 2 because 2 heroes are always together
            xp_available += (data_base['monsters'][monster_name]['xp'] / 2)

    return xp_available


def can_level_up(data_base, hero):
    """
    Returns true if hero can level up

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    hero: name of the hero to check (str)

    Returns
    -------
    can_level_up: true if hero can level up (bool)

    Version
    -------
    specification:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)
    implementation:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)

    """
    hero_level = data_base['heroes'][hero]['level']
    hero_xp = data_base['heroes'][hero]['xp']
    #xp needed to level up [level 1, level 2,...]
    xp_needed = [0, 100, 200, 400, 800]

    if hero_level != 5:
        #Check if there is enough for hero to level up.
        if (get_xp_available(data_base) - (xp_needed[hero_level]-hero_xp)) >= 0:
            return True
    
    return False


def someone_on_hill(data_base, ia_team):
    """
    Returns True if an enemy is on hill
    
    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    ia_team: color of ia team (str)

    Returns
    -------
    on_hill: true if enemy on hill (bool)

    Version
    -------
    specification:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)
    implementation: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)
    
    """
    #Loop on hero
    for hero in data_base['heroes']:

        #Check if enemy hero is on hill
        if data_base['heroes'][hero]['position'] in data_base['hill']\
        and data_base['heroes'][hero]['team'] != ia_team:
    
            return True
    
    return False


def enemy_in_range(data_base, hero):
    """
    Returns a list of enemy heroes in range of hero

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    hero: hero to check range (str)

    Returns
    -------
    enemies_in_range: list of enemy heroes in range of hero (list)

    Version
    -------
    specification:
    implementation:

    """
    enemies_in_range = []

    #Loop on hero (=target)
    for hero_name in data_base['heroes']:

        #Check if targetted hero is in range of hero
        #Check that hero is an enemy
        #Check hero is alive
        if check_in_range_hero(data_base, hero, 'heroes', hero_name)\
        and data_base['heroes'][hero]['team'] != data_base['heroes'][hero_name]['team']\
        and check_hp(data_base, hero_name, 'heroes'):

            #Add hero to list of enemies in range
            enemies_in_range.append(hero_name)

    return enemies_in_range


def get_monster_in_range(data_base, hero):
    """
    Returns a list of monsters in range of basic attack of hero

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    hero: name of the hero to check (str)

    Returns
    -------
    monsters_in_range: list of monsters next to hero (list)

    Version
    --------
    specification:
    implementation:
    """
    #Initialize list of monsters in range
    monsters_in_range = []

    #Loop on monsters
    for monster in data_base['monsters']:

        #Check if monster is next to hero
        #check if monster is alive
        if check_in_range_hero(data_base, hero, 'monsters', monster)\
        and check_hp(data_base, monster, 'monsters'):

            #Add monster to the list
            monsters_in_range.append(monster)

    return monsters_in_range


def free_hill_case(data_base):
    """
    Returns a list with the free cases of hill

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)

    Returns
    -------
    free_hill: list of all free cases (list)

    Version
    -------
    specification:
    implementation:
    """
    #Initialize list of free cases
    free_hill = []

    #Loop on cases of hill
    for hill_case in data_base['hill']:
        #Check nobody is on the case
        if not check_case_occupied(data_base, hill_case):
            #Add case to the list if nobody on it
            free_hill.append(hill_case)
    
    return free_hill


def get_ia_actions(data_base, ia_team):
    """
    Returns a string with actions of ia heroes

    Parameters
    ----------
    data_base: dico with all informations about the game (dict)
    ia_team: color of ia team (str)

    Returns
    -------
    ia_actions: actions of ia heroes (str)

    Version
    -------
    specification: Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)
    implementation:  Antoine Mouchet, Simon Willame, Blandine Willemart (v1 03/05/19)

    """
    #Initialize variables
    mage_action = False
    ia_actions = ''
    hero_classes = {}
    enemy_heroes = []

    #get list of free cases on hill
    free_hill = free_hill_case(data_base)

    #Loop on hero
    for hero in data_base['heroes']:
        
        #Check if hero is in the team of ia
        if data_base['heroes'][hero]['team'] == ia_team:
            hero_classes[data_base['heroes'][hero]['class']] = hero
        else:
            enemy_heroes.append(hero)


    #Loop on hero
    for hero in data_base['heroes']:
        #Get class of hero
        hero_class = data_base['heroes'][hero]['class']
        hero_level = data_base['heroes'][hero]['level']

        #Get enemies in range of hero
        enemies_in_range = enemy_in_range(data_base, hero)
    
        #Get focus
        if len(enemies_in_range) != 0:
            focus = get_focus(data_base, enemies_in_range)

        #Check if hero is in team of ia
        if data_base['heroes'][hero]['team'] == ia_team:
            
            #Check if hero is a barbarian
            if hero_class == 'barbarian':

                #Check if there is at least one enemy hero in range
                if len(enemies_in_range) != 0:

                    #Attack hero to focus
                    ia_actions += '%s:*%d-%d ' % \
                    (hero, data_base['heroes'][focus]['position'][0], data_base['heroes'][focus]['position'][1])

                #FARMING SIMULATOR STATE
                elif can_level_up(data_base, hero):

                    #Get monster to focus
                    close_monsters = get_closest_monster(data_base, hero)
                    focus = get_focus_monster(data_base, close_monsters)

                    #If distance is 1: attack
                    if close_monsters[focus] == 1:
                        ia_actions += '%s:*%d-%d ' % \
                        (hero, data_base['monsters'][focus]['position'][0], data_base['monsters'][focus]['position'][1])

                    #if distance > 1: move toward monster
                    elif close_monsters[focus] > 1:

                        #Get case to reach
                        position_hero = get_direction_entity(data_base, hero, 'monsters', focus)
                        #Movement of barbarian
                        ia_actions += '%s:@%d-%d ' % (hero, position_hero[0], position_hero[1])

                #REACH HILL AND PROTECT IT STATE
                else:
                    barb_action = False

                    #If barbarian not on hill, try to reach it
                    if data_base['heroes'][hero]['position'] not in data_base['hill']:

                        #try to occupy the whole hill
                        if len(free_hill) != 0:
                            position_hero = get_direction_entity(data_base, hero, 'case', case_coords=free_hill[0])
                        
                        #if no free case, reach closest one
                        else:
                            position_hero = get_direction_entity(data_base, hero, 'case', case_coords=data_base['hill'][0])
            
                        #Movement of barbarian
                        ia_actions += '%s:@%d-%d ' % (hero, position_hero[0], position_hero[1])
                    
                    #Barbarian is on hill
                    elif not barb_action:

                        #Check if an enemy is on the hill too
                        if someone_on_hill(data_base, data_base['heroes'][hero]['team']):

                            #Loop on enemies
                            for enemy in enemy_heroes:

                                #Check if enemy is on hill
                                if data_base['heroes'][enemy]['position'] in data_base['hill'] and not barb_action:

                                    #Get position to reach enemy her
                                    position_hero = get_direction_entity(data_base, hero, 'heroes', enemy)
                                    #Move
                                    ia_actions += '%s:@%d-%d ' % (hero, position_hero[0], position_hero[1])
                                    barb_action = True
                                
                        #try to use stun
                        #Check spell is not in cooldown
                        #Check hero is at least level 3
                        elif data_base['heroes'][hero]['cooldown2'] == 0 and hero_level >= 3:

                            for enemy in enemy_heroes:

                                #If barbarian in range to use stunt on at least one enemy
                                if check_in_range_hero(data_base, hero, 'heroes', enemy, spell='stun'):

                                    #Use spell
                                    ia_actions += '%s:stun ' % hero
                                    barb_action = True

                        #try to use invigorate
                        #check spell is not in cooldown
                        #Check hero is at least level 2
                        elif data_base['heroes'][hero]['cooldown1'] == 0 and hero_level >= 2:
                
                                    #Use spell
                                    ia_actions += '%s:invigorate ' % hero
                                    barb_action = True

            #Check if hero is an healer
            elif hero_class == 'healer':
                #Check if healer is behind barbarian
                if check_in_range_hero(data_base, hero, 'heroes', hero_classes['barbarian']):

                    #Check if hero is at least level 3 and cooldown of second spell is null
                    if hero_level >= 3 and data_base['heroes'][hero]['cooldown2'] == 0:

                        #Use immunise spell
                        ia_actions += '%s:immunise:%d-%d ' %\
                        (hero, data_base['heroes'][hero_classes['barbarian']]['position'][0],\
                        data_base['heroes'][hero_classes['barbarian']]['position'][1])
                    
                    #Check if hero is at least level 2 and cooldown of first spell is null
                    elif hero_level >= 2 and data_base['heroes'][hero]['cooldown1'] == 0:
                        ia_actions += '%s:invigorate ' % hero
                    
                else:
                    #try to reach barbarian
                    barb_pos = get_direction_entity(data_base, hero, 'heroes', hero_classes['barbarian'])
                    ia_actions += '%s:@%d-%d ' % (hero, barb_pos[0], barb_pos[1])

            #Check if hero is a mage
            elif hero_class == 'mage':

                #Loop on enemy heroes
                for enemy in enemy_heroes:

                    #If mage in range to use fulgura
                    if check_in_range_hero(data_base, hero, 'heroes', enemy, spell='fulgura') and\
                    data_base['heroes'][hero]['cooldown1'] == 0 and not mage_action and hero_level >= 2:

                        #Use spell
                        ia_actions += '%s:fulgura:%d-%d ' %\
                        (hero, data_base['heroes'][enemy]['position'][0], data_base['heroes'][enemy]['position'][1])
                        #Mage did something
                        mage_action = True
            
                #Check if there is at least 1 hero in range and if both spells are in cooldown
                if len(enemies_in_range) != 0 and data_base['heroes'][hero]['cooldown1'] != 0 and\
                data_base['heroes'][hero]['cooldown2'] != 0 and not mage_action:

                    #Attack
                    ia_actions += '%s:*%d-%d ' %\
                    (hero, data_base['heroes'][focus]['position'][0], data_base['heroes'][focus]['position'][1])
                    #Mage did something
                    mage_action = True

                #Check if someone is on hill
                elif someone_on_hill(data_base, ia_team) and not mage_action:
                    #get position to reach
                    position_hero = get_direction_entity(data_base, hero, 'case', case_coords=data_base['hill'][0])
                    #Movement
                    ia_actions += '%s:@%d-%d ' % (hero, position_hero[0], position_hero[1])
                    #Mage did something
                    mage_action = True

                #If nobody on hill then follow the healer
                else:
                    position_hero = get_direction_entity(data_base, hero, 'heroes', hero_classes['healer'])
                    ia_actions += '%s:@%d-%d ' % (hero, position_hero[0], position_hero[1])

            #Check if hero is a rogue
            elif hero_class == 'rogue':
  
                #Get list of monsters in range
                monsters_in_range = get_monster_in_range(data_base, hero)
                 
                #Check if rogue is on hill
                if data_base['heroes'][hero]['position'] not in data_base['hill']:

                    #Go to hill
                    if len(free_hill) != 0:
                        position_hero = get_direction_entity(data_base, hero, 'case', case_coords=free_hill[0])

                        #if no free case, reach closest one
                    else:
                        position_hero = get_direction_entity(data_base, hero, 'case', case_coords=data_base['hill'][0])
                    
                    #Movement
                    ia_actions += '%s:@%d-%d ' % (hero, position_hero[0], position_hero[1])

                

                 #Check if there are heroes or monsters in range of basic attack
                elif len(enemies_in_range) != 0 or len(monsters_in_range) != 0:

                    #Check if rogue is at least level 3, use burst if it's the case
                    if hero_level >= 3:
                        ia_actions += '%s:burst ' % hero
                    
                    #Use basic attack
                    elif len(enemies_in_range) == 0:
                        #Hit first monster
                        focus = monsters_in_range[0]

                        #Use basic attack    
                        ia_actions += '%s:*%d-%d ' %\
                        (hero, data_base['monsters'][focus]['position'][0], data_base['monsters'][focus]['position'][1])
                    
                    else:
                        ia_actions += '%s:*%d-%d ' %\
                        (hero, data_base['heroes'][focus]['position'][0], data_base['heroes'][focus]['position'][1])
                    

    return ia_actions



