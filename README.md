# Pokémon Team Building

This project uses [`poke-env`](https://github.com/hsahovic/poke-env) to simulate Pokémon battles and evaluate AI-designed teams.
A **Genetic Algorithm (GA)** is implemented to automatically design and improve teams based on simulated win rates.

------------------------------------------------------------------------

## Installation

### 1. Clone the Repository

Clone this repository and its submodules. The `--recurse-submodules` flag is important as it will automatically clone the `pokemon-showdown` repository needed for the simulator.

```bash
git clone --recurse-submodules https://github.com/cantafionathan/pokemon.git
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

The `pokemon-showdown` directory is already included as a git submodule. You need to set it up before running the battles.

Ensure you have Node.js v10+ installed.

Open a new terminal and run the following commands from the project root:

```bash
# Navigate into the submodule directory
cd pokemon-showdown

# Install server dependencies
npm install

# Set up the configuration file
cp config/config-example.js config/config.js

# Start the server
node pokemon-showdown start --no-security
```

The `--no-security` flag disables crucial security features buts its useful for AI training as it removes rate limiting and authentication. Use with caution.

`node pokemon-showdown start --no-security` starts a local Showdown server on `ws://localhost:8000`, which `poke-env` will connect to.

## Running the BO Loop

In a separate terminal, with your virtual environment activated, run:

``` bash
python main.py
```

### Notes

-   Ensure pokemon-showdown is running before starting main.py
-   All battles occur locally — no online authentication is required
-   For Gen 1 formats, make sure each Pokémon line includes Ability: None (required by Showdown parsing)

## Data Sources

[raw_teams.txt](https://gist.github.com/scheibo/7c9172f3379bbf795a5e61a802caf2f0)

[pokemon-embeddings](https://huggingface.co/datasets/minimaxir/pokemon-embeddings)