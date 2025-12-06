# data_processing/gen1/get_movelist.py
import csv
import re
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup


# -------------------------
# INPUT MOVE LIST (only id, move)
# -------------------------

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


def scrape_serebii(move_name: str) -> dict:
    """
    Scrape Gen 1 move fields that are reliably accessible:
      - Power
      - PP
      - Accuracy
      - Type (from Battle Type table link)
    """

    # URL slug rules
    if move_name.strip().lower() == "sand attack":
        url_name = "sand-attack"
    else:
        url_name = move_name.lower().replace(" ", "")

    url = f"https://www.serebii.net/attackdex-rby/{url_name}.shtml"
    print(f"Scraping: {move_name} → {url}")

    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        print(f"  ERROR {resp.status_code}: skipping")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extract the info table with Power Points, Base Power, Accuracy
    info_table = None
    for tbl in soup.find_all("table", class_="dextable"):
        rows = tbl.find_all("tr")
        for r in rows:
            cells = [c.get_text(" ", strip=True) for c in r.find_all("td")]
            if len(cells) >= 3 and cells[0] == "Power Points" and cells[1] == "Base Power":
                info_table = tbl
                break
        if info_table:
            break

    if not info_table:
        print(f"  Could not locate stats table for {move_name}")
        return None

    # Extract power, pp, accuracy
    rows = info_table.find_all("tr")
    PP = ""
    power = ""
    accuracy = ""

    i = 0
    while i < len(rows):
        cols = [c.get_text(" ", strip=True) for c in rows[i].find_all("td")]
        if len(cols) >= 3 and cols[0] == "Power Points":
            if i + 1 < len(rows):
                vals = [c.get_text(" ", strip=True) for c in rows[i+1].find_all("td")]
                if len(vals) >= 3:
                    PP, power, accuracy = vals[:3]
            i += 2
            continue
        i += 1

    # Now extract the Battle Type from the 4th table (index 3)
    tables = soup.find_all("table")
    battle_type = ""
    if len(tables) >= 4:
        try:
            battle_type_cell = tables[3].find_all("tr")[1].find_all("td")[1]
            a_tag = battle_type_cell.find("a")
            if a_tag and a_tag.has_attr("href"):
                import re
                href = a_tag["href"]
                m = re.search(r"/type/(\w+)\.shtml", href)
                if m:
                    battle_type = m.group(1).lower()
        except Exception as e:
            print(f"  Warning: could not extract type for {move_name}: {e}")

    return {
        "power": power,
        "pp": PP,
        "accuracy": accuracy,
        "type": battle_type,
    }


def parse_move_list(text: str):
    moves = []
    for line in text.strip().splitlines()[1:]:
        parts = line.split(",", 1)  # only split into 2 parts: id, name
        if len(parts) != 2:
            continue
        move_id = int(parts[0])
        name = parts[1].strip()
        moves.append((move_id, name))
    return moves


def main():
    output_path = Path("data/gen1/movelist.csv")

    moves = parse_move_list(MOVE_LIST)
    results = []

    for move_id, name in moves:
        scraped = scrape_serebii(name)

        if scraped is None:
            scraped = {"power": "", "pp": "", "accuracy": "", "type": ""}

        results.append({
            "id": move_id,
            "name": name,
            "type": scraped["type"],
            "power": scraped["power"],
            "pp": scraped["pp"],
            "accuracy": scraped["accuracy"],
        })

        time.sleep(1)  # be polite to Serebii

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name", "type", "power", "pp", "accuracy"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✓ Wrote {len(results)} moves → {output_path}")


if __name__ == "__main__":
    main()
