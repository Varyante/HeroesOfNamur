"""
Module made by Clement Delzotti (@cdelzotti) to save logs about the game.
"""

import shutil
import os

def save_initiate(hon_file):
    if not os.path.isdir('save'):
        os.mkdir('save')

    game_index = -1
    leave_loop = False
    while not leave_loop:
        game_index += 1
        if not os.path.isdir('save/%d/' % game_index):
            leave_loop = True

    fh = open('save/game_index', 'w+')
    fh.write(str(game_index))
    fh.close()
    os.mkdir('save/%d' % game_index)
    shutil.copyfile(hon_file, 'save/%d/map' % game_index)

def save_command(command, player, turn_id):
    fh = open('save/game_index', 'r')
    game_index = fh.readlines()
    fh.close()

    game_index = int(game_index[0])

    fh = open('save/%d/logs' % game_index, 'a+')
    fh.write('%d: %s~%s\n' % (turn_id, player, command))
    fh.close()
