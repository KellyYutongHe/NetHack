import random
import sys

RADIUS = int(sys.argv[1])

ROWS = 25
COLS = 80


print("poop")
while True:
    r = raw_input()
    if r == 'end':
        #end signals we died or whatever
        print "exiting"
        break
    else:
        #game is still going
	
	level = raw_input()
	hp = raw_input()

        #read map
        gameMap = []
        for i in range(0,ROWS):
            line = raw_input()
            gameMap.append(line)
	
	x = raw_input()
	y = raw_input()

        #read neighborhood
        nb = []
        for i in range(0,RADIUS*2+1):
            line = raw_input()
            nb.append(line)

        print random.choice(['level_prev','level_next','move_N','move_NE','move_E','move_SE','move_S','move_SW','move_W','move_NW','rest','open_door','search','kick'])
