import collections
import logging
import numpy as np
import os
import pty
import random
import re
import select
import tempfile

import vt102

import sys
import string
from subprocess import Popen, PIPE
import random

ROWS = 25
COLS = 80

NUM_ITERS = int(sys.argv[1])


class CMD:
    class DIR:
        NW, N, NE, E, SE, S, SW, W = 'ykulnjbh'
        UP, DOWN = '<>'

    APPLY, CLOSE, DROP, EAT, ENGRAVE, FIRE, INVENTORY, OPEN = 'acdeEfio'
    PAY, PUTON, QUAFF, QUIVER, READ, REMOVE, SEARCH, THROW = 'pPqQrRst'
    TAKEOFF, WIELD, WEAR, EXCHANGE, ZAP, CAST, PICKUP, WAIT = 'TwWxzZ,.'

    MORE = '\x0d'      # ENTER
    KICK = '\x04'      # ^D  ####?
    TELEPORT = '\x14'  # ^T

    class SPECIAL:
        CHAT = '#chat'
        DIP = '#dip'
        FORCE = '#force'
        INVOKE = '#invoke'
        JUMP = '#jump'
        LOOT = '#loot'
        MONSTER = '#monster'
        OFFER = '#offer'
        PRAY = '#pray'
        RIDE = '#ride'
        RUB = '#rub'
        SIT = '#sit'
        TURN = '#turn'
        WIPE = '#wipe'


class InventoryItem:
    CATEGORIES = ('Amulets', 'Weapons', 'Armor', 'Comestibles',
                  'Scrolls', 'Spellbooks', 'Potions', 'Rings',
                  'Wands', 'Tools', 'Gems')

    def __init__(self, raw):
        self.raw = raw.strip()

    def __str__(self):
        return self.raw

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self)

    @property
    def is_cursed(self):
        return re.search(r'\bcursed\b', self.raw)

    @property
    def is_uncursed(self):
        return re.search(r'\buncursed\b', self.raw)

    @property
    def is_blessed(self):
        return re.search(r'\bblessed\b', self.raw)

    @property
    def is_being_worn(self):
        return re.search(r'\(being worn\)', self.raw)

    @property
    def is_in_use(self):
        return re.search(r'\((?:in use|lit)\)', self.raw)

    @property
    def duplicates(self):
        m = re.match(r'^(\d+)', self.raw)
        if not m:
            return 1
        return int(m.group(1))

    @property
    def charges(self):
        m = re.match(r'\((\d+):(\d+)\)', self.raw)
        if not m:
            return None, None
        return int(m.group(1)), int(m.group(2))

    @property
    def enchantment(self):
        m = re.match(r' ([-+]\d+) ', self.raw)
        if not m:
            return None
        return int(m.group(1))

    @property
    def named(self):
        m = re.match(r' named ([^\(]+)', self.raw)
        if not m:
            return None
        return m.group(1)


class AmuletsItem(InventoryItem):
    pass


class ArmorItem(InventoryItem):
    pass


class WeaponsItem(InventoryItem):
    @property
    def is_wielded(self):
        return re.search(r'\(weapon in hands?\)', self.raw)

    @property
    def is_alternate(self):
        return re.search(r'\(alternate weapon; not wielded\)', self.raw)

    @property
    def is_quivered(self):
        return re.search(r'\(in quiver\)', self.raw)


class ComestiblesItem(InventoryItem):
    pass


class ScrollsItem(InventoryItem):
    pass


class SpellbooksItem(InventoryItem):
    pass


class PotionsItem(InventoryItem):
    pass


class RingsItem(InventoryItem):
    pass


class WandsItem(InventoryItem):
    pass


class ToolsItem(InventoryItem):
    pass


class GemsItem(InventoryItem):
    pass


class Player:
    OPTIONS = ('CHARACTER={character}\n'
               'OPTIONS=hilite_pet,pickup_types:$?+!=/,'
               'gender:{gender},race:{race},align:{align}')

    def __init__(self, **kwargs):
        ######
        self.action_count = 0
        self.only_maps = True
        self.RADIUS = 4
        self.queued_action = None
        self.process = Popen(['python', '-u', 'agent423.py', str(self.RADIUS)], stdout=PIPE, stdin=PIPE, bufsize=1)
        self.hp = 15
	self.level = 1
	######

        self._stream = vt102.stream()
        self._screen = vt102.screen((ROWS, COLS))
        self._screen.attach(self._stream)

        self._need_inventory = True
        self._has_more = False
        self._command = None

        self.messages = collections.deque(maxlen=1000)
        self.stats = {}
        self.inventory = {}
        self.spells = {}


        opts = dict(character=random.choice('bar pri ran val wiz'.split()),
                    gender=random.choice('mal fem'.split()),
                    race=random.choice('elf hum'.split()),
                    align=random.choice('cha neu'.split()))
        opts.update(kwargs)

        #handle = tempfile.NamedTemporaryFile(delete=False)
        #handle.write(self.OPTIONS.format(**opts).encode('utf-8'))
        #handle.flush()
        # os.chmod(handle.name, 0666)
        # os.environ['NETHACKOPTIONS'] = '@' + handle.name

    def play(self):
        name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        pty.spawn(['/home/yhe29/nethack/nethack', '-u', name], self._observe, self._act)

    def choose_action(self):
        raise NotImplementedError

    def choose_answer(self):
        raise NotImplementedError

    def neighborhood(self, radius=4):
        radius=4
	x, y = self._screen.cursor()

        ylo, yhi = y - radius, y + radius + 1
        xlo, xhi = x - radius, x + radius + 1
        ulo, uhi = 0, 2 * radius + 1
        vlo, vhi = 0, 2 * radius + 1

	#fill out of board spaces w/ ''
	#if y < radius:
        #    ylo, yhi = 0, 2*radius+1   ###we always want same dimensions
        #if x < radius:
        #    xlo, xhi = 0, 2*radius+1
        #if y > ROWS - radius-1:
        #    ylo, yhi =  ROWS - (2*radius+1),ROWS
        #if x > COLS - radius-1:
        #    xlo, xhi = COLS - (2*radius+1),COLS

	hood = np.zeros((2 * radius + 1, 2 * radius + 1), np.dtype(int))
        # print(self._screen.display)
        # hood[ulo:uhi, vlo:vhi] = self._screen.display[ylo:yhi][xlo:xhi]
        # print(xlo,xhi,ylo,yhi,ulo,uhi,vlo,vhi)
	for i in range(ulo,uhi):
            for j in range(vlo,vhi):
		if ylo+i >= ROWS or ylo + i < 0 or xlo + j >= COLS or xlo + j < 0:
			hood[i][j] = ord(' ')
                else:
			hood[i][j] = ord(self._screen.display[ylo+i][xlo+j])
        return hood, x,y

    def _parse_inventory(self, raw):
        found_inventory = False
        for category in InventoryItem.CATEGORIES:
            klass = eval('%sItem' % category)
            contents = self.inventory.setdefault(category, {})
            i = raw.find(category.encode('utf-8'))
            if i > 0:
                s = raw[i:].split(b'\x1b[7m')[0]
                for letter, name in re.findall(br' (\w) - (.*?)(?=\x1b\[)', s):
                    contents[letter.decode('utf-8')] = klass(name.decode('utf-8'))
                if not self.only_maps:
                    logging.error('inventory for %s: %s', category, contents)
                    print('inventory for %s: %s', category, contents)

                found_inventory = True
        self._need_inventory = not found_inventory

    def _parse_glyphs(self, raw):
        self._stream.process(raw)



        logging.info('current map:\n')
        for i in range(len(self._screen.display)):
            logging.info( self._screen.display[i])
            # print( self._screen.display[i])
        #logging.warn('current neighborhood:\n%s', '\n'.join(
        #    ''.join(chr(c) for c in r) for r in self.neighborhood(3)))

        message = ''

        self._parse_message()
        self._parse_attributes()
        self._parse_stats()

    def _parse_message(self):
        '''Parse a message from the first line on the screen.'''
        l = self._screen.display[0]
        if l.strip() and l[0].strip():
            if not self.only_maps:
                logging.warn('message: %s', l)
                print('message: %s', l)
            self.messages.append(l)

    def _parse_attributes(self):
        '''Parse character attributes.'''
        l = self._screen.display[22]
        m = re.search(r'St:(?P<st>[/\d]+)\s*'
                      r'Dx:(?P<dx>\d+)\s*'
                      r'Co:(?P<co>\d+)\s*'
                      r'In:(?P<in>\d+)\s*'
                      r'Wi:(?P<wi>\d+)\s*'
                      r'Ch:(?P<ch>\d+)\s*'
                      r'(?P<align>\S+)', l)
        if m:
            self.attributes = m.groupdict()
            if not self.only_maps:
                logging.warn('parsed attributes: %s', ', '.join('%s: %s' % (
                    k, self.attributes[k]) for k in sorted(self.attributes)))

                print('parsed attributes: %s', ', '.join('%s: %s' % (
                    k, self.attributes[k]) for k in sorted(self.attributes)))

    def _parse_stats(self):
        '''Parse stats from the penultimate line.'''
        l = self._screen.display[23]
        m = re.search(r'Dlvl:(?P<dlvl>\S+)\s*'
                      r'\$:(?P<money>\d+)\s*'
                      r'HP:(?P<hp>\d+)\((?P<hp_max>\d+)\)\s*'
                      r'Pw:(?P<pw>\d+)\((?P<pw_max>\d+)\)\s*'
                      r'AC:(?P<ac>\d+)\s*'
                      r'Exp:(?P<exp>\d+)\s*'
                      r'(?P<hunger>Satiated|Hungry|Weak|Fainting)?\s*'
                      r'(?P<stun>Stun)?\s*'
                      r'(?P<conf>Conf)?\s*'
                      r'(?P<blind>Blind)?\s*'
                      r'(?P<burden>Burdened|Stressed|Strained|Overtaxed|Overloaded)?\s*'
                      r'(?P<hallu>Hallu)?\s*', l)
        if m:
            self.stats = m.groupdict()
            for k, v in self.stats.items():
                if v and v.isdigit():
                    self.stats[k] = int(v)
            if not self.only_maps:
                logging.warn('parsed stats: %s', ', '.join(
                    '%s: %s' % (k, self.stats[k]) for k in sorted(self.stats)))

    def _observe(self, raw):
        logging.warn("OBSERVING")
        self._parse_glyphs(raw)
        if self._command is CMD.INVENTORY:
            if not self._has_more:
                self.inventory = {}
            self._parse_inventory(raw)
        if self.stats.has_key('dlvl'):
	    self.level=self.stats['dlvl']
	if self.stats.has_key('hp'):
	    self.hp = self.stats['hp']
	self._command = None
        self._has_more = b'-More-' in raw or b'(end)' in raw

    def _act(self):
        logging.warn("ACTING")

        msg = self.messages and self.messages[-1] or ''
        logging.warn("Message = "  + msg)

        if self._has_more or '-More-' in msg and 'ynq' not in msg:
            self._command = CMD.MORE
            self.messages.append('')
        elif 'You die' in msg or 'ynq' in msg:
            self._command = 'q'
            self.choose_action(True)
        elif self.queued_action != None:
            if self.queued_action == 'CHOOSE':
                self._command = self.choose_answer()
                self.messages.append('')
            else:
                self._command = self.queued_action
            self.queued_action = None
        elif '? ' in msg and ' written ' not in msg:
            logging.warn('detected question!!!')
            self._command = self.choose_answer()
            self.messages.append('')

            # self.queued_action = '.'
        # elif self._need_inventory:
            # self._command = CMD.INVENTORY
        else:
            self._command = self.choose_action()

        if self.action_count == 0:
            self._command = 'y'
        elif self.action_count == 1:
            self._command = CMD.MORE

        self.action_count += 1


        logging.warn('sending command "%s"', self._command)
        # print('sending command "%s"', self._command)


        #### FIX BOUNDARY CONDITIONS IN NEIGHBORHOOD

        return self._command


class RandomMover(Player):
    def choose_answer(self):
        return 'n'

    def choose_action(self, end=False):
        if end:
            print >>self.process.stdin, 'end'
            return 'end'
        print >>self.process.stdin, 'continue'

	print >>self.process.stdin, str(self.level)
	print >>self.process.stdin, str(self.hp)

        for j in range(0,25):
            print >>self.process.stdin, ''.join(self._screen.display[j]) # write input

        nb,x,y = self.neighborhood(self.RADIUS)
	#nb = np.zeros((9,9))

	print >>self.process.stdin, x
	print >>self.process.stdin, y

        for j in range(0,2*self.RADIUS+1):
            print >>self.process.stdin, ''.join([chr(i) for i in nb[j]])

        self.process.stdin.flush() # not necessary in this case

        action = self.process.stdout.readline().rstrip() # read output

        if action == 'level_prev':
            return '<'
        elif action == 'level_next':
            return '>'
        elif action == 'move_N':
            return 'k'
        elif action == 'move_NE' :
            return 'u'
        elif action == 'move_E':
            return 'l'
        elif action == 'move_SE':
            return 'n'
        elif action == 'move_S' :
            return 'j'
        elif action == 'move_SW':
            return 'b'
        elif action == 'move_W':
            return 'h'
        elif action == 'move_NW':
            return 'y'
        elif action == 'rest' :
            return '.'
        elif action == 'open_door':
            self.queued_action = self.get_door_direction()
            return 'o'
        elif action == 'search':
            return 's'
        elif action == 'kick':
            self.queued_action = self.get_door_direction()
            return CMD.KICK

    def get_door_direction(self):
        nb,x,y = self.neighborhood(self.RADIUS)
        playerPos = self.RADIUS  #center of 2*radius + 1 square
        if nb[playerPos][playerPos + 1] == '+':
            return 'k'
        if nb[playerPos+1][playerPos + 1] == '+':
            return 'u'
        if nb[playerPos+1][playerPos] == '+':
            return 'l'
        if nb[playerPos+1][playerPos - 1] == '+':
            return 'n'
        if nb[playerPos][playerPos - 1] == '+':
            return 'j'
        if nb[playerPos-1][playerPos - 1] == '+':
            return 'b'
        if nb[playerPos - 1][playerPos] == '+':
            return 'h'
        if nb[playerPos  - 1][playerPos + 1] == '+':
            return 'y'
        else:
            return 'k'


# drain all available bytes from the given file descriptor, until a complete
# timeout goes by with no new data.
def _drain(fd, timeout=0.01):
    more, _, _ = select.select([fd], [], [], timeout)
    buf = b''
    while more:
        buf += os.read(fd, 1024)
        more, _, _ = select.select([fd], [], [], timeout)
    return buf


# we almost want to do what pty.spawn does, except that we know how our child
# process works. so, we forever loop: read world state from nethack, then issue
# an action to nethack. repeat.
def _copy(fd, observe, act):
    while True:
        buf = _drain(fd)
        if buf:
            observe(buf)
            os.write(1, buf)
        pty._writen(fd, act().encode('utf-8'))


# monkeys ahoy !
pty._copy = _copy


if __name__ == '__main__':

    count = 0
    while count < NUM_ITERS:
        count+=1

        logging.basicConfig(stream=open('nethack-bot-' + str(count) +'.log', 'w'),level=logging.DEBUG,format='%(levelname).1s %(asctime)s %(message)s')
        rm = RandomMover()
        rm.play()
