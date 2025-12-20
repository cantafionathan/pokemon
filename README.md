# Pokémon Team Building

This project uses [`poke-env`](https://github.com/hsahovic/poke-env) to simulate Pokémon battles and study the **combinatorial optimization task of team building.**

It implements and compares

 - a **Genetic Algorithm (GA)**
 - a **Randoms Search (RS)** baseline

Battles are executed by connecting to a **local Pokémon Showdown server**, included as a git submodule.

------------------------------------------------------------------------

## Requirements
 - **Python 3.9+**
 - **Node.js 10+**

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

`node pokemon-showdown start --no-security` starts a local Showdown server at `ws://localhost:8000`, which `poke-env` will connect to.

## Running experiments

Experiments are launched via `main.py`.

To see all available arguments, run:

```bash
python main.py --help
```

To see all available arguments for a given experiment, run:
```bash
python main.py --experiment \<experiment_name\> --help
```

### Example: GA vs RS in gen1OU with plots

```bash
python main.py --experiment ga_vs_rs --tier OU --plot --team-evo-method EloRandomSearch
```

This will:

 1. Run the selected experiment (`ga_vs_rs`) 
 2. Save logs to the `logs/` directory
 3. The `--plot` tag generates aggregate performance plots
 4. the`--team-evo-method` argument is an optional addition to `--plot` which launches an **interactive team evolution viewer**

### Logging & plotting
  - Logs are written to structed directories under `logs/`
  - Each run records:
    - full team specification
    - total battles used
    - scores
    - and other info
  - Each experiment has the option to provide its own plotting method
  - For example, `plot_ga_vs_rs.py` loads logs automatically and produces
    - score vs generation
    - score vs battles
    - optional interactive team evolution viewer

## Data Sources

[Fortelle's Pokémon Learnsets](https://raw.githubusercontent.com/Fortelle/pokemon-learnsets/master/dist/)

[Smogon Gen 1 Tier data](https://raw.githubusercontent.com/smogon/pokemon-showdown/master/data/mods/gen1/formats-data.ts)

[Bulbapedia](https://bulbapedia.bulbagarden.net/wiki/)
