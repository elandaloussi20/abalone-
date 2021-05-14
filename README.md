##  Abalone-AI (Définition) 
Abalone-AI est un agent de jeu intelligent , on  discute de l'implémentation de l'agent de jeu en utilisant plusieurs algorithmes d'intelligence artificielle.  

## Artificial intelligence algorithms
Au total, on a implémenté une algorithme  qui est  couramment utilisée dans les jeux à somme nulle comme Abalone . 

**1.** Minimax  
 

### Representation de jeux 
Contrairement à de nombreux jeux de société, Abalone utilise une grille hexagonale qu'il n'est pas possible de représenter avec un système de coordonnées cartésien ou matriciel comme cela est fait avec des planches carrées.


Les coordonnées sont lues en termes de colonnes diagonales (x) et de lignes horizontales (z). Les colonnes augmentent en diagonale, tandis que les lignes augmentent verticalement. Les coordonnées d'une seule bille sont exprimées sous la forme d'un tuple nommé avec deux 
entrées:

> Hex(x=−3, z=1)
Lors du déplacement, un tuple avec le même format est ajouté à la coordonnée qui décalera la coordonnée dans cette direction:

> Hex(−3, 1) + Direction (1,0) = Hex(−2,1)  
> * Billes  simple se déplaçant dans la direction (1,0) *

De même, les groupes de billes (ceux qui sont adjacents les uns aux autres et peuvent être déplacés ensemble) sont représentés de la même manière, sauf sous forme de liste:

> True: [Hex(0,0),Hex(0,1),Hex(0,2)], where True = white piece  
> False: [Hex(1,0),Hex(1,1),Hex(1,2)], where False = black piece

**Enfin, pour une représentation complète de l'état du tableau, nous ajoutons chaque groupe de billes à une table de hachage:**


> {  
> True: [Hex(0,0),Hex(0,1),Hex(0,2)],  
> False: [Hex(1,0),Hex(1,1),Hex(1,2)]  
> }  

### Fonction heuristique et d'évaluation
Les heuristiques utilisées par certains des algorithmes sont décrites ci-dessous:

#### Proximité du centre (h <sub> 1 </sub>)

Abalone  nécessite des mouvements très défensifs. Être au centre du plateau est le meilleur endroit car cela force l'adversaire vers les bords, qui est l'endroit le plus vulnérable du plateau. La distance entre chaque bille au centre de la grille est calculée pour les deux joueurs, puis leur différence est prise (le maximizer favorise les h <sub> 1 </sub> bas).

#### Cohesion (h<sub>2</sub>)
Les billes plus rapprochées forment une population, qui est l'ensemble des billes adjacentes. Plus il y a de cohésion, moins il y a de populations. Il est idéal pour un joueur d'avoir le minimum de populations et de garder ses billes ensemble. La cohésion est mesurée par la distance entre toutes les billes (le maximiseur favorise les faibles (h <sub> 2 </sub>).

#### Billes à bord  (h<sub>3</sub>)
La dernière heuristique est donnée par la différence de nombre de billes sur le plateau. C'est une heuristique offensive plutôt qu'une heuristique défensive comme les précédentes. Il est donné par la différence de billes entre les deux joueurs (le maximiseur favorise un h <sub> 3 </sub> élevé).

La fonction d'évaluation est donc la somme des scores donnés par toutes les heuristiques: * eval = h <sub> 1 </sub> + h <sub> 2 </sub> + h <sub> 3 </sub> *

> * J'ai découvert par essai une erreur que h <sub> 2 </sub> doit être utilisé lorsque les billes sont loin du centre: | h <sub> 1 </sub> | > 2 et h <sub> 3 </sub> doivent être utilisés lorsque les billes sont proches du centre: | h <sub> 1 </sub> | <1.8, et lorsque h <sub> 3 </sub> est utilisé, h <sub> 3 </sub> est mis à l'échelle d'un facteur 100 pour que les coups d'attaque soient favorisés. *

### Optimisations 
L'ordre des mouvements et les tables de transposition sont extrêmement importants pour que les meilleurs chemins soient recherchés en premier.

#### Trois d'affilée
La quantité de façons d'avoir trois blocs d'affilée est également idéale. Cette heuristique sera utilisée pour l'ordre des déplacements.

#### Push movuvements  
Les états qui conduisent à potentiellement plus de poussées réduiront le nombre de mouvements nécessaires pour gagner la partie. Donc, cette heuristique est bonne pour l'ordre des mouvements.



## Résultas
Dans l'ensemble, la recherche de variation principale avec l'optimisation de la table de transposition a donné les meilleurs résultats, tandis que Minimax a obtenu les moins bons résultats. Monte-Carlo Tree Search n'était pas testable sur notre machine.


# Éxecution de code 

##  Générer un fichier d'état
Ouvrez `dump.py` et remplissez le modèle d'état du jeu et exécutez le programme en utilisant l'interpréteur Python. Le programme produira un fichier JSON qui peut être chargé dans le programme principal et utilisé soit pour générer le prochain meilleur coup, soit pour simuler un jeu à partir de cet état.

##  Configurer l'agent de jeu
1.Ouvrez `abalone / config.py` et définissez le tableau de départ initial en remplissant les valeurs de votre choix (la valeur par défaut est` mini` pour une version miniaturisée du jeu à des fins de démonstration)
2. La taille de la grille peut être modifiée en utilisant `GRID_RADIUS`
3. Le nombre de billes requis pour gagner peut être modifié en utilisant `GAME_OVER`
4. Le nombre maximum de billes attaquantes dans une ligne peut être modifié en utilisant `GROUP_LENGTHS` (la valeur par défaut est` 3`)
5.  Les états des joueurs peuvent également être modifiés en utilisant`BLACK` et `WHITE` (default: `BLACK = False`, `WHITE = True`)

## Running the game agent
1. Installer les dépendances: `python setup.py develop`
2. Run : `start.py` et suivez l'interface de ligne de commande pour charger un JSON state (voir Générer un fichier state) ou simuler un jeu entre deux ordinateurs IA dans un jeu d'Abalone

