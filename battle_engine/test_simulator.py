from .battle_simulator import evaluate_team

# Example: a Showdown-format Gen 1 team
example_team = """
Gengar
Ability: None
- Hypnosis
- Thunderbolt
- Explosion
- Psychic

Chansey
Ability: None
- Thunder Wave
- Soft Boiled
- Ice Beam
- Seismic Toss

Tauros
Ability: None
- Body Slam
- Blizzard
- Hyper Beam
- Earthquake

Exeggutor
Ability: None
- Sleep Powder
- Psychic
- Stun Spore
- Explosion

Snorlax
Ability: None
- Body Slam
- Self Destruct
- Reflect
- Rest

Starmie
Ability: None
- Thunder Wave
- Blizzard
- Recover
- Thunderbolt
"""

winrate = evaluate_team(example_team, n_battles_per_opponent=1)
print(f"Estimated winrate: {winrate:.2f}")
