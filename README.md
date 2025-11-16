# Pokémon BO

This project uses [`poke-env`](https://github.com/hsahovic/poke-env) to simulate Pokémon battles and evaluate AI-designed teams.\
A **Bayesian Optimization (BO)** framework is implemented to automatically design and improve teams based on simulated win rates.

------------------------------------------------------------------------

## Installation

Clone the repository:

``` bash
git clone https://github.com/cantafionathan/pokemon.git
cd pokemon
```

Create and activate a virtual environment

``` bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

## Setting up `poke-env`

`poke-env` requires a local Pokémon Showdown server. Ensure you have Node.js v10+ installed.

If this is your first setup, open a new terminal and run:

``` bash
git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown
npm install
cp config/config-example.js config/config.js
node pokemon-showdown start --no-security
```

The `--no-security` flag disables crucial security features, use with caution. This flag facilitates AI training by removing rate limiting and authentication requirements

This starts a local Showdown server on ws://localhost:8000, which poke-env will connect to.

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