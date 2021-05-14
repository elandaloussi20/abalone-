"""
Gère la représentation des hexagones (tuiles), des groupes hexadécimaux et des grilles de plateau et aussi
met en œuvre toute la logique des mouvements légaux.
"""
import math
import random
import itertools as it
from numbers import Number
from operator import itemgetter
from functools import wraps
from collections import namedtuple

from . import config
from .utils import split_when

class IllegalMove(Exception):
    pass

HexBase = namedtuple('Hex', ('x', 'z'))

class Hex(HexBase):
    """
     Representation of a hex or tile on the grid.
    """

    directions = [(_x, _z) for _x, _z in  # Collide with attrs
                  it.permutations((-1, 0, 1), 2)]

    @property
    def y(self):
        return -self.x - self.z

    def __add__(self, other):
        return Hex(*[s + o for s, o in zip(self, other)])

    def __rmul__(self, other):
        return self.__mul__(other)

    def __mul__(self, other):
        if isinstance(other, Number):
            return Hex(*[other*axis for axis in self])
        return super(Hex, self).__mul__(other)

    def __neg__(self):
        return Hex(*[-axis for axis in self])

    def neighbours(self):
        """
        Renvoie un itérateur avec tous les hexagones environnants.
        """
        for x, z in self.directions:
            yield Hex(x=self.x + x, z=self.z + z)

    def distance(self, hex):
        """
        Renvoie la distance de déplacement à partir de l'hexagone spécifié.
        """
        return (abs(self.x - hex.x) +
                abs(self.y - hex.y) +
                abs(self.z - hex.z)) / 2

    def is_adjacent(self, hex):
        """
        Renvoie si l'autre hexadécimal est adjacent à ça .
        """
        return self.distance(hex) == 1

    def direction(self, hex):
        """
        Returns the direction from this Hex to the other.
        """
        return (hex.x - self.x, hex.z - self.z)


class HexBlock(tuple):
    def __new__(cls, *args):
        return super(HexBlock, cls).__new__(cls, *args)

    def is_valid(self):
        """
        Renvoie si ce HexBlock est valide:
            - il doit avoir une longueur valide.
            - tous les hexs doivent être adjacents les uns aux autres.
            - tous les hexagones doivent être alignés dans la même direction.
        """
        return all((
            # Doit avoir une longueur valide
            len(self) in config.GROUP_LENGTHS,
            # Doit être adjacents l'un à l'autre
            all((a.is_adjacent(b) for a, b in zip(self, self[1:]))),
            # Doit être dans la même direction
            len(set((a.direction(b) for a, b in zip(self, self[1:])))) <= 1
        ))

    @property
    def directions(self):
        """
        Renvoie les directions d'alignement de ce HexBlock:
            - toutes les directions possibles si le bloc est un seul hex.
            - les deux sens d'alignement s'il est fait de plus d'un
            hex.        """
        if len(self) == 1:
            for direction in Hex.directions:
                yield direction
        else:
            transition = zip(self, self[1:])
            for a, b in transition:
                yield a.direction(b)
                yield b.direction(a)

    def strength(self, direction):
        """
        Renvoie la force de poussée dans une direction donnée: le nombre d'hexagones
        aligné dans cette direction
        """
        return len(self) if direction in self.directions else 1

    def sorted(self, direction):
        """
        
        Renvoie un HexBlock trié dans la direction spécifiée.
        """
        axis = next((pos for axis, pos in enumerate(direction)))
        return HexBlock(sorted(self, key=itemgetter(axis)))


def queryset(func):
    """
    Renvoie un objet Hex QuerySet à partir d'un itérateur de Hexes.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        results = func(self, *args, **kwargs)
        results = ((hex, self[hex]) for hex in results)
        return HexQuerySet(results)
    return wrapper


class HexQuerySet(dict):
    def __init__(self, states):
        for hex, state in states:
            self[hex] = state

    @queryset
    def neighbours(self, hex):
        """
        
        Renvoie les voisins d'un hexadécimal.
        """
        return (neighbour for neighbour in hex.neighbours()
                if neighbour in self)

    @queryset
    def by_state(self, state):
        """
        Filtre le jeu de requêtes par état  (player colour).
        """
        return (hex for (hex, s) in self.items() if s == state)

    @queryset
    def not_empty(self):
        """
        Filtre tous les hexagones vides.
        """
        return (hex for (hex, s) in self.items() if s is not None)

    @queryset
    def by_axis(self, x=None, z=None):
        """
        Renvoie des hexagones sur les axes spécifiés.
        """
        for hex, state in self.items():
            if all((x is None or hex.x == x, z is None or hex.z == z)):
                yield hex

    @queryset
    def by_vector(self, hex, direction, distance):
        """
        Renvoie tous les hexagones dans une certaine direction et jusqu'à une certaine distance
        commençant sur l'hexagone spécifié.
        """
        moves = ((axis*step for axis in direction) for step in range(distance))
        places = (hex + move for move in moves)
        return set(self.keys()) & set(places)

    def populations(self, state):
        """
        Renvoie des ensembles d'hexagones interconnectés..
        """
        unchecked = set(self.by_state(state).keys())
        while unchecked:
            neighbours = {unchecked.pop()}
            group = set()
            while neighbours:
                hex = neighbours.pop()
                unchecked.discard(hex)
                group.add(hex)
                neighbours.update(set(hex.neighbours()) & unchecked)
            yield group

    @queryset
    def population(self, hex):
        """
        Renvoie l'ensemble des hexagones interconnectés où se trouve l'hexagone spécifié.
        """
        return next((pop for pop in self.populations(self[hex]) if hex in pop))

    def are_connected(self):
        """
        Renvoie si les hexagones QS actuels sont tous connectés ou non.
        """
        # Vérifiez que tous les hexagones sont soit blancs ou noirs
        states = set(self.values())
        if len(states) != 1 or states == {None}:
            return False
        populations = self.populations(states.pop())
        return len(list(populations)) == 1

    def hex_blocks(self, hex, lengths=None):
        """
        Renvoie tous les blocs possibles dans lesquels cet hex peut être déplacé.
        """
        if lengths is None:
            lengths = config.GROUP_LENGTHS

        blocks = set()
        population = self.population(hex)
        neighbours = population.neighbours(hex)
        directions = (hex.direction(n) for n in neighbours)
        directions = it.chain(directions, [(0, 0, 0)])

        for direction, distance in it.product(directions, lengths):
            block = population.by_vector(hex, direction, distance)
            block = HexBlock(block.keys())

            #  Trier les blocs pour assurer la proximité
            if all(hex[1] == block[0][1] for hex in block):
                block = HexBlock(tuple(sorted(block, key=itemgetter(0))))
            else:
                block = HexBlock(tuple(sorted(block,key=itemgetter(1))))

            blocks.add(block)
        return blocks

    def blocks(self, state, lengths=None):
        """
        Renvoie tous les blocs possibles qui pourraient être légalement déplacés.
        """
        return {HexBlock(block) for hex in self.by_state(state)
                for block in self.hex_blocks(hex, lengths)}

    @queryset
    def move(self, block, direction):
        """
        Tente de déplacer le bloc donné dans la direction donnée en montant et en
        Exception IllegalMove si ce n'est pas possible car:
            - le bloc spécifié n'est pas correct.
            - la direction spécifiée n'est pas correcte.
            - il n'y a pas assez de place pour déplacer les billes.
            - l'ennemi est plus fort.
            - certaines billes se suicideraient.
        """
        if direction not in Hex.directions:
            raise IllegalMove("Incorrect direction")

        if not block.is_valid():
            raise IllegalMove("Incorrect block.")

        # Réorganiser le bloc
        block = block.sorted(direction)

        state = self[block[0]]

        # Obtenez la force de poussée
        strength = block.strength(direction)

        # Obtenez le miroir du bloc dans cette direction
        mirror = (hex + strength*Hex(*direction) for hex in block)

        # Fendre le miroir sur la première bille non ennemie
        enemies, others = split_when(lambda h: self.get(h, None) != (not state), mirror)

        # Il doit y avoir moins de billes ennemies que mes billes
        if not len(block) > len(enemies):
            raise IllegalMove("Enemy is stronger.")

        new_block = set((hex + Hex(*direction) for hex in block))
        
        if direction not in block.directions:
            # Broadside move
            # Interdire les Broadside moves si un hexagone de destination n'est pas vide           
                raise IllegalMove("Pas assez de place pour déplacer les billes ennemies")
        else:
            # Straight/side move
            # Obtenez la première position hexadécimale dans la direction vers laquelle le bloc se dirige
            diff = list(new_block.difference(block))
            if diff[0] in others:
                # Refuser straight/side se déplace si le premier hexagone de destination est sa propre bille
                if self.get(diff[0]) is not None:
                    raise IllegalMove("Straight/Side: Attaquer sa propre bille.")
            elif diff[0] in enemies:
                # Sumito move
                # Effacez toutes les billes propres et ennemies
                for hex in it.chain(block, enemies):
                    self[hex] = None

                new_enemies = [(hex + direction, not state) for hex in enemies
                            if hex + direction in self]
                self.update(new_enemies)
        
        # Effacez toutes les billes
        for hex in block:
            self[hex] = None
        
        new_block = [(hex + direction, state) for hex in block]
        if any((hex not in self for hex, state in new_block)):
            raise IllegalMove("Tenter de sortir de la grille.")
        self.update(new_block)
        return self.keys()

    def marbles(self, state, length=False):
        """
        Renvoie le nombre de billes pour un joueur donné.
        """
        marbles = {k: v for k, v in self.items() if v == state}
        if length:
            return len(marbles)
        return marbles
    
    def check_win(self, state):
        """
        Vérifie si la partie est terminée
        (le joueur adverse a perdu> =  GAME_OVER billes)
        """
        if len(self.marbles(not state)) <= config.GAME_OVER:
            return True
        return False
    
    def center_proximity(self, state):
        """
        Renvoie la distance moyenne de chaque bille à
        l'origine de la grille, pour un joueur donné.
        """
        center = Hex(0,0)

        distance = -math.inf
        marbles = self.marbles(state)
        for marble in marbles.keys():
            if distance == -math.inf:
                distance = marble.distance(center)
            else:
                distance += marble.distance(center)
        
        return distance / len(marbles)
    
    def mean_position(self, state):
        """
        Renvoie la position moyenne d'un joueur.
        """
        pops = list(self.populations(state))
        avg_hex = -math.inf

        for pop in pops:
            length = len(pop)
            d_avg = sum(d for d, _ in pop) / length
            r_avg = sum(r for _, r in pop) / length
            avg_hex = Hex(d_avg, r_avg)
        
        return avg_hex
    
    def chase(self, state):
        # Obtenir la position moyenne actuelle 
        avg = self.mean_position(state)

        # Obtenir le plus petit pop d'un autre joueur
        pops = list(self.populations(not state))
        pops = sorted(pops, key=lambda x: len(x))
        pop = [pops[0]]
        avg_other = Hex(0,0)

        # Calculer la position du plus petit pop
        for block in pop:
            length = len(block)
            d_avg = sum(d for d, _ in block) / length
            r_avg = sum(r for _, r in block) / length
            avg_other = Hex(d_avg, r_avg)
        
        return avg.distance(avg_other)
    






class BaseGrid(dict):
    BLACK = config.BLACK
    WHITE = config.WHITE
    REPR = {
        BLACK: 'B',
        WHITE: 'W',
        None: '.',
    }

    def __init__(self, r):
        self.radius = r
        for x in self.axis_range():
            for z in self.axis_range(x):
                self[Hex(x=x, z=z)] = None

    @property
    def query(self):
        return HexQuerySet(self.items())

    def axis_range(self, v=0):
        """
        Renvoie la plage de positions dans l'axe spécifié.
        """
        r = self.radius
        start = max(-r-v, -r)
        stop = min(r-v, r)
        return range(start+1, stop)

    @property
    def display(self):
        board = ((self.REPR[self[(x, z)]] for x in self.axis_range(z))
                 for z in self.axis_range())
        board = (' '.join(row).center(self.radius*4) for row in board)
        return '\n'.join(list(board))
    
    def deep_copy(self,raw=False):
        copy = {
                config.WHITE: [(k[0], k[1]) for k, v in self.items() if v == config.WHITE],
                config.BLACK: [(k[0], k[1]) for k, v in self.items() if v == config.BLACK],
        }
        if raw == True:
            return copy
        return AbaloneGrid(copy)

    def move(self, block, direction):
        """
        Tente de déplacer un bloc dans une direction en augmentant une exception
        de mouvement interdit si ce mouvement est interdit.
        """
        for block, state in self.query.move(block, direction).items():
            self[block] = state

    def moves(self, state, rnd=False, seed=None):
        """
        Renvoie tous les mouvements possibles pour certains joueurs.
        """
        lengths = config.GROUP_LENGTHS
        if rnd:
            lengths = random.randrange(lengths[0], lengths[1])
            lengths = range(lengths, lengths + 1)
        if seed:
            if seed.__class__.__name__ == 'method':
                random.seed = seed
            else:
                random.seed(seed)
        
        blocks = list(self.query.blocks(state, lengths))
        for block in blocks:
            for direction in Hex.directions:
                try:
                    self.query.move(block, direction)
                except IllegalMove:
                    pass
                else:
                    yield block, direction





class AbaloneGrid(BaseGrid):
    def __init__(self, initial_position):
        super(AbaloneGrid, self).__init__(config.GRID_RADIUS)
        positions = {position: state
                     for state, positions in initial_position.items()
                     for position in positions}
        self.update(positions)
