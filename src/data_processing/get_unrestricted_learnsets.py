#!/usr/bin/env python3
import json
import requests
from pathlib import Path
from io import StringIO
import csv

FORTELLE_URLS = [
    "https://raw.githubusercontent.com/Fortelle/pokemon-learnsets/master/dist/redgreen.json",
    "https://raw.githubusercontent.com/Fortelle/pokemon-learnsets/master/dist/yellow.json",
]

POKEMON_TIERS_PATH = Path("data/pokemon_tiers.json")
OUTPUT_PATH = Path("data/learnsets.json")

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

def load_pokedex_from_tiers(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Convert list to dict keyed by id
    return {entry["id"]: {"name": entry["name"], "tier": entry["tier"]} for entry in data}

def load_movelist_from_string(move_list_str):
    moves = {}
    f = StringIO(move_list_str.strip())
    for row in csv.DictReader(f):
        moves[int(row["id"])] = row["move"]
    return moves

def load_fortelle_learnsets():
    print("Fetching Fortelle learnsets...")
    all_entries = []
    for url in FORTELLE_URLS:
        data = requests.get(url).json()
        all_entries.extend(data)

    by_id = {}
    for entry in all_entries:
        pid = int(entry["pokemon"])
        if pid not in by_id:
            # Start with the first entry
            by_id[pid] = {
                "pokemon": pid,
                "moves": entry.get("moves", [])
            }
        else:
            # Append moves from other entries for the same Pokemon
            existing_moves = by_id[pid]["moves"]
            new_moves = entry.get("moves", [])
            existing_moves.extend(new_moves)
            by_id[pid]["moves"] = existing_moves

    # Optional: remove duplicate moves per Pokémon, since you can have duplicates after merging
    for pid, data in by_id.items():
        seen = set()
        unique_moves = []
        for move_entry in data["moves"]:
            key = (move_entry.get("move"), move_entry.get("method"), move_entry.get("level"))
            if key not in seen:
                seen.add(key)
                unique_moves.append(move_entry)
        data["moves"] = unique_moves

    return by_id


def build_final_learnsets(pokedex, movelist, fortelle_by_id):
    print("Building final learnsets…")
    output = {}

    for pid, info in pokedex.items():
        name = info["name"]
        tier = info["tier"]

        if pid not in fortelle_by_id:
            print(f"Warning: {name} has no Fortelle entry")
            output[pid] = {"name": name, "tier": tier, "learned": []}
            continue

        entry = fortelle_by_id[pid]
        natural_moves = []
        inherited_moves = []

        for m in entry["moves"]:
            mid = int(m["move"])

            if "pokemon" in m and int(m["pokemon"]) != pid:
                inherited_moves.append({
                    "move": mid,
                    "method": "evolution",
                    "level": None
                })
            else:
                natural_moves.append({
                    "move": mid,
                    "method": m["method"],
                    "level": m.get("level")
                })

        natural_ids = {m["move"] for m in natural_moves}
        inherited_filtered = [m for m in inherited_moves if m["move"] not in natural_ids]
        combined = natural_moves + inherited_filtered

        # Deduplicate here by move id ONLY, ignoring method and level:
        seen_move_ids = set()
        unique_moves = []
        for m in combined:
            if m["move"] not in seen_move_ids:
                seen_move_ids.add(m["move"])
                unique_moves.append(m)

        formatted = []
        for m in unique_moves:
            mid = m["move"]
            formatted.append({
                "move_id": mid,
                "move_name": movelist.get(mid, f"Move{mid}"),
            })

        output[pid] = {
            "name": name,
            "tier": tier,
            "learned": formatted
        }

    return output


def main():
    pokedex = load_pokedex_from_tiers(POKEMON_TIERS_PATH)
    movelist = load_movelist_from_string(MOVE_LIST)
    fortelle = load_fortelle_learnsets()

    learnsets = build_final_learnsets(pokedex, movelist, fortelle)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(learnsets, f, indent=2)

    print(f"Saved: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
