# Pokémon Team Building

This project uses [`poke-env`](https://github.com/hsahovic/poke-env) to simulate Pokémon battles and attempt the combinatorial optimization task of team building. A **Genetic Algorithm (GA)** is implemented for this task. To run the battles, it connects to a local Pokémon Showdown server (included as a git submodule).

------------------------------------------------------------------------

## Installation

### 1. Clone the repository with submodules

Clone this repository and its submodules. The `--recurse-submodules` flag is important as it will automatically clone the `pokemon-showdown` repository needed for the simulator.

```bash
git clone --recurse-submodules https://github.com/cantafionathan/pokemon
cd pokemon
```

Note: If you have already cloned the repository without the `--recurse-submodules` flag, you can run this command after cloning: `git submodule update --init --recursive`


### 2. Create and activate a virtual environment

``` bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies:

``` bash
pip install -r requirements.txt
```

## Setting up the Pokémon Showdown Server

The `pokemon-showdown` repo is already included as a git submodule. You need to set it up before running the battles.

Ensure you have Node.js v10+ installed.

Open a new terminal and run the following commands from the project root:

```bash
cd pokemon-showdown
npm install
cp config/config-example.js config/config.js
node pokemon-showdown start --no-security
```

> The `--no-security` flag disables crucial security features buts its useful for AI training as it removes rate limiting and authentication. Use with caution.

`node pokemon-showdown start --no-security` starts a local Showdown server on `ws://localhost:8000`, which `poke-env` will connect to.


## Data Sources

[Fortelle's Pokémon Learnsets](https://raw.githubusercontent.com/Fortelle/pokemon-learnsets/master/dist/)
[Smogon Gen 1 Tier data](https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen1/formats-data.ts)
