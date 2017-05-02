#!/usr/bin/env python

# NOTE: This is not really working right now

import random
import sys
from pprint import pprint
from copy import deepcopy

RADIUS = int(sys.argv[1])

ROWS = 25
COLS = 80

LEVEL_DOWN = 0
EXPLORE = 1
NONE = 2

MOVES = ('level_prev', 'level_next', 'move_N', 'move_NE', 'move_E', 'move_SE',
	'move_S', 'move_SW', 'move_W', 'move_NW', 'rest', 'open_door', 'search'
	'kick')

DIRECTIONS = {
	(-1, -1): 'move_NW',
	(-1, 0): 'move_N',
	(-1, 1): 'move_NE',
	(0, -1): 'move_W',
	(0, 1): 'move_E',
	(1, -1): 'move_SW',
	(1, 0): 'move_S',
	(1, 1): 'move_SE'
}

CHARS = {
	' ': {
		'empty': False,
		'priority': EXPLORE
	},
	'.': {
		'empty': True,
		'test': 1,
		'priority': NONE
	},
	'-': {
		'empty': False,
		'priority': NONE
	},
	'|': {
		'empty': False,
		'priority': NONE
	},
	'#': {
		'empty': True,
		'priority': NONE
	},
	'+': {
		'empty': True,
		'priority': NONE
	},
	'x': {
		'empty': True,
		'priority': NONE
	},
	'd': {
		'empty': True,
		'priority': NONE
	},
	'u': {
		'empty': True,
		'priority': NONE
	},
	'f': {
		'empty': True,
		'priority': NONE
	},
	'e': {
		'empty': False,
		'priority': NONE
	},
	'$': {
		'empty': True,
		'priority': NONE
	},
	'@': {
		'empty': False,
		'priority': NONE
	},
	'>': {
		'empty': True,
		'priority': LEVEL_DOWN
	},
	'<': {
		'empty': True,
		'priority': NONE
	},
	'!': {
		'empty': False,
		'priority': NONE
	}
}

f = open('new_log','w')

def log(*args):
	global f
	for arg in args:
		pprint(arg, stream=f)
		f.flush()

def gen_map(gameMap, x, y):
	def bufFunc(r, c):
		if r == -1 or c == -1 or r == ROWS or c == COLS:
			return '!'
		return gameMap[r][c]

	bufMap = [[bufFunc(r, c) for c in range(-1, COLS + 1)] for r in range(-1, ROWS + 1)]

	def func(r, c):
		char = bufMap[r][c]
		if char not in CHARS:
			char = '!'
		obj = deepcopy(CHARS[char])
#		if char == '-':
#			if bufMap[r][c - 1] != '-' and bufMap[r][c - 1] != '-':
#				log(("empty", (r, c)))
#				obj['empty'] = True
#		elif char == '|':
#			if bufMap[r - 1][c] != '|' or bufMap[r][c + 1] == '|':
#				log(("empty", (r, c)))
#				obj['empty'] = True
		return obj

	mymap = [[func(r, c) for c in range(COLS + 2)] for r in range(ROWS + 2)]
	return mymap

def dfs(mymap, best_moves, x, y, depth):
	best = (None, (mymap[x][y]['priority'], depth))
	if best_moves[x][y][1] is not None and best[1] >= best_moves[x][y][1]:
		return best_moves[x][y][1]

	best_moves[x][y] = best

	for delta in sorted(list(DIRECTIONS.keys())):
		a, b = x + delta[0], y + delta[1]
		spot = mymap[a][b]

		# log(("spot", (a, b), spot, depth))

		if (spot['priority'], depth) < best[1]:
			result = (spot['priority'], depth)
			best = (delta, result)
		elif spot['empty']:
			# log("searching")
			next_result = dfs(mymap, best_moves, a, b, depth + 1)
			if next_result < best[1]:
				best = (delta, next_result)

	log(("best", (x, y), best, depth))
	best_moves[x][y] = best
	return best[1]

mymap = 1

def update_map(mymap, new_map, x, y):
	for r in range(ROWS):
		for c in range(COLS):
			obj = mymap[r][c]
			obj['empty'] = new_map[r][c]['empty']
			obj['priority'] = max(obj['priority'], new_map[r][c]['priority'])

def get_move(gameMap, nbhd, x, y):
	global mymap
	x += 1
	y += 1
	if mymap == 1:
		mymap = 2
		return 'rest'
	elif mymap == 2:
		mymap = gen_map(gameMap, x, y)
	else:
		if mymap[x][y]['priority'] == LEVEL_DOWN:
			return 'level_next'
		new_map = gen_map(gameMap, x, y)
		update_map(mymap, new_map, x, y)
	best_moves = [[(None, None) for _ in range(COLS + 2)] for _ in range(ROWS +
		2)]
	dfs(mymap, best_moves, x, y, 1)
	move = best_moves[x][y][0]
	if type(move) == str:
		return move
	if move in DIRECTIONS.keys():
		dest_x, dest_y = x + move[0], y + move[1]
		while True:
			next_move = best_moves[dest_x][dest_y][0]
			if next_move not in DIRECTIONS.keys():
				log(("dest", dest_x, dest_y))
				break
			dest_x += next_move[0]
			dest_y += next_move[1]
		a, b = x + move[0], y + move[1]
		if mymap[a][b]['priority'] == EXPLORE:
			mymap[a][b]['priority'] = NONE
		return DIRECTIONS[move]
	assert False
	if move is None:
		result = best_moves[x][y][1]
		if result[0] == LEVEL_DOWN:
			return 'level_next'
	assert False

#print "Dont delete this"

def main():
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

			x = int(raw_input())
			y = int(raw_input())

			#read neighborhood
			nb = []

			for i in range(0,RADIUS*2+1):
				line = raw_input()
				nb.append(line)

			log(gameMap, (y + 1, x + 1))

			move = get_move(gameMap, nb, y, x)
			log(("move", move))
			assert move in MOVES
			print move

if __name__ == '__main__':
	main()
