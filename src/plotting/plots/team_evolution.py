import matplotlib.pyplot as plt
import matplotlib.patches as patches
import requests
from io import BytesIO
from PIL import Image
from pathlib import Path
import numpy as np
from matplotlib.widgets import Button
from plotting.utils import load_move_names, load_pokedex_from_tiers

POKEDEX = load_pokedex_from_tiers()
MOVE_NAMES = load_move_names()
SPRITE_DIR = Path("plotting/sprites")

_sprite_cache: dict[int, Image.Image | None] = {}


def get_local_sprite(pokemon_id: int) -> Image.Image | None:
    """
    Load a locally saved sprite for a Pokémon ID.
    Caches results in memory.
    """
    if pokemon_id in _sprite_cache:
        return _sprite_cache[pokemon_id]

    sprite_path = SPRITE_DIR / f"{pokemon_id}.png"
    if not sprite_path.exists():
        _sprite_cache[pokemon_id] = None
        return None

    try:
        img = Image.open(sprite_path).convert("RGBA")
        _sprite_cache[pokemon_id] = img
        return img
    except Exception as e:
        print(f"Warning: could not load sprite {pokemon_id}: {e}")
        _sprite_cache[pokemon_id] = None
        return None



def plot_team_evolution(run, entry, ax):
    """
    Plot one team onto the given Axes `ax`.
    Does NOT call plt.show().
    """
    ax.clear()
    ax.axis("off")

    pokemon_ids, movesets = entry.team
    num_pokemon = len(pokemon_ids)

    cols = min(num_pokemon, 3)
    rows = (num_pokemon + cols - 1) // cols

    # Title info
    title = f"Format: {run.format}    Method: {run.method}    Seed: {run.run_seed}    Generation: {entry.generation}"
    ax.text(0.5, 1.05, title, ha="center", va="bottom", fontsize=16, transform=ax.transAxes)
    ax.text(
        0.5,
        1.00,
        f"Score: {entry.score:.4f}    Battles used: {entry.total_battles_used}",
        ha="center",
        va="bottom",
        fontsize=12,
        transform=ax.transAxes,
    )

    for i, (pid, moves) in enumerate(zip(pokemon_ids, movesets)):
        col = i % 3
        row = i // 3

        x = col * 1.5 + 0.5
        y = 0.9 - row * 0.9

        pokemon_data = POKEDEX.get(pid)
        if pokemon_data:
            pokemon_display_name = f"{pokemon_data['name']}, {pokemon_data['tier']}"
        else:
            pokemon_display_name = f"Pokémon {pid}"

        moves_named = [MOVE_NAMES.get(m, str(m)) for m in moves]

        # Draw name
        ax.text(x + 0.75, y + 0.05, pokemon_display_name, ha="center", va="top", fontsize=12, weight="bold")

        # Get and plot sprite
        sprite = get_local_sprite(pid)
        sprite_x = x + 0.1
        sprite_y = y - 0.15
        sprite_size = 0.6

        if sprite:
            ax.imshow(sprite, extent=(sprite_x, sprite_x + sprite_size, sprite_y - sprite_size, sprite_y))
        else:
            ax.add_patch(patches.Rectangle((sprite_x, sprite_y - sprite_size), sprite_size, sprite_size, fill=True, color="gray"))
            ax.text(sprite_x + sprite_size / 2, sprite_y - sprite_size / 2, "No Sprite", ha="center", va="center", fontsize=8, color="red")

        # Moveset text (with names)
        moves_text = "\n".join(moves_named)
        ax.text(x + 0.8, sprite_y - 0.1, moves_text, ha="left", va="top", fontsize=10, family="monospace")

    ax.set_xlim(0, cols * 1.6 + 0.5)
    ax.set_ylim(-rows * 1.5, 1.2)


class TeamNavigator:
    def __init__(self, run, entries):
        self.run = run
        self.entries = entries
        self.index = 0

        self.fig, self.ax = plt.subplots(figsize=(10, 5))
        plt.subplots_adjust(bottom=-0.4)
        self.ax.axis("off")

        # Buttons axes
        axprev = plt.axes([0.3, 0.05, 0.1, 0.075])
        axnext = plt.axes([0.6, 0.05, 0.1, 0.075])

        self.bprev = Button(axprev, 'Previous')
        self.bnext = Button(axnext, 'Next')

        self.bprev.on_clicked(self.prev)
        self.bnext.on_clicked(self.next)

        self.plot_current()

        plt.show()

    def plot_current(self):
        plot_team_evolution(self.run, self.entries[self.index], self.ax)
        self.fig.canvas.draw_idle()

    def next(self, event):
        self.index = (self.index + 1) % len(self.entries)
        self.plot_current()

    def prev(self, event):
        self.index = (self.index - 1) % len(self.entries)
        self.plot_current()
