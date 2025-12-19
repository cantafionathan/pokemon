from collections import defaultdict
from typing import Dict, List, Tuple
import numpy as np
from pathlib import Path
import json

from .models import RunLog


def group_runs_by_method(runs: List[RunLog]) -> Dict[str, List[RunLog]]:
    by_method = defaultdict(list)
    for run in runs:
        by_method[run.method].append(run)
    return by_method


def mean_and_se(values: List[float]) -> Tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    mean = arr.mean()
    if len(arr) > 1:
        se = arr.std(ddof=1) / np.sqrt(len(arr))
    else:
        se = 0.0
    return mean, se

POKEMON_TIERS_PATH = Path("data/pokemon_tiers.json")
MOVE_LIST = r"""
id,move
1,Pound
2,Karate Chop
3,Double Slap
4,Comet Punch
5,Mega Punch
6,Pay Day
7,Fire Punch
8,Ice Punch
9,Thunder Punch
10,Scratch
11,Vice Grip
12,Guillotine
13,Razor Wind
14,Swords Dance
15,Cut
16,Gust
17,Wing Attack
18,Whirlwind
19,Fly
20,Bind
21,Slam
22,Vine Whip
23,Stomp
24,Double Kick
25,Mega Kick
26,Jump Kick
27,Rolling Kick
28,Sand Attack
29,Headbutt
30,Horn Attack
31,Fury Attack
32,Horn Drill
33,Tackle
34,Body Slam
35,Wrap
36,Take Down
37,Thrash
38,Double-Edge
39,Tail Whip
40,Poison Sting
41,Twineedle
42,Pin Missile
43,Leer
44,Bite
45,Growl
46,Roar
47,Sing
48,Supersonic
49,Sonic Boom
50,Disable
51,Acid
52,Ember
53,Flamethrower
54,Mist
55,Water Gun
56,Hydro Pump
57,Surf
58,Ice Beam
59,Blizzard
60,Psybeam
61,Bubble Beam
62,Aurora Beam
63,Hyper Beam
64,Peck
65,Drill Peck
66,Submission
67,Low Kick
68,Counter
69,Seismic Toss
70,Strength
71,Absorb
72,Mega Drain
73,Leech Seed
74,Growth
75,Razor Leaf
76,Solar Beam
77,Poison Powder
78,Stun Spore
79,Sleep Powder
80,Petal Dance
81,String Shot
82,Dragon Rage
83,Fire Spin
84,Thunder Shock
85,Thunderbolt
86,Thunder Wave
87,Thunder
88,Rock Throw
89,Earthquake
90,Fissure
91,Dig
92,Toxic
93,Confusion
94,Psychic
95,Hypnosis
96,Meditate
97,Agility
98,Quick Attack
99,Rage
100,Teleport
101,Night Shade
102,Mimic
103,Screech
104,Double Team
105,Recover
106,Harden
107,Minimize
108,Smokescreen
109,Confuse Ray
110,Withdraw
111,Defense Curl
112,Barrier
113,Light Screen
114,Haze
115,Reflect
116,Focus Energy
117,Bide
118,Metronome
119,Mirror Move
120,Self-Destruct
121,Egg Bomb
122,Lick
123,Smog
124,Sludge
125,Bone Club
126,Fire Blast
127,Waterfall
128,Clamp
129,Swift
130,Skull Bash
131,Spike Cannon
132,Constrict
133,Amnesia
134,Kinesis
135,Soft-Boiled
136,Hi Jump Kick
137,Glare
138,Dream Eater
139,Poison Gas
140,Barrage
141,Leech Life
142,Lovely Kiss
143,Sky Attack
144,Transform
145,Bubble
146,Dizzy Punch
147,Spore
148,Flash
149,Psywave
150,Splash
151,Acid Armor
152,Crabhammer
153,Explosion
154,Fury Swipes
155,Bonemerang
156,Rest
157,Rock Slide
158,Hyper Fang
159,Sharpen
160,Conversion
161,Tri Attack
162,Super Fang
163,Slash
164,Substitute
165,Struggle
"""

def load_pokedex_from_tiers():
    with open(POKEMON_TIERS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    # Convert list to dict keyed by id
    return {entry["id"]: {"name": entry["name"], "tier": entry["tier"]} for entry in data}

def load_move_names():
    lines = MOVE_LIST.strip().split("\n")
    header = lines[0].split(",")
    move_map = {}
    for line in lines[1:]:
        parts = line.split(",")
        move_id = int(parts[0])
        move_name = parts[1]
        move_map[move_id] = move_name
    return move_map
