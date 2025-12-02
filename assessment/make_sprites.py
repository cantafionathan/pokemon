import json
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Gen 1 (Red/Blue) sprite URL pattern from PokeAPI repo
GEN1_SPRITE_URL = (
    "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-i/red-blue/{}.png"
)

# --- Helper: convert species → dex number using PokeAPI ---
def fetch_dex_number(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()["id"]

# --- Fetch authentic Gen 1 R/B sprite ---
def fetch_gen1_sprite(species):
    dex = fetch_dex_number(species)
    url = GEN1_SPRITE_URL.format(dex)
    r = requests.get(url)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGBA")
    return img


# --- Draw a single Pokémon block ---
def draw_pokemon_block(draw, canvas, x, y, species, moves, sprite, f_name, f_moves):
    # Resize sprite
    target_h = 120
    ratio = target_h / sprite.height
    sprite_resized = sprite.resize((int(sprite.width * ratio), target_h), Image.NEAREST)

    canvas.paste(sprite_resized, (x, y), sprite_resized)

    # Species name
    y_name = y + target_h + 5
    draw.text((x, y_name), species, fill=(0, 0, 0), font=f_name)

    # Move list
    y_move = y_name + 26
    for mv in moves:
        draw.text((x, y_move), f"• {mv}", fill=(50, 50, 50), font=f_moves)
        y_move += 22


# --- Load a team directly from your experiment JSON file ---
def load_team_from_json(path):
    with open(path, "r") as f:
        data = json.load(f)
    return data["final_team"]


# --- Main renderer ---
def make_team_card_from_json(json_path, output="team.png"):
    team = load_team_from_json(json_path)

    W, H = 800, 600
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Fonts
    font_name = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 26)
    font_moves = ImageFont.truetype("/Library/Fonts/Arial.ttf", 20)

    # 2×3 layout
    cols = 3
    col_w = W // cols
    row_h = H // 2

    positions = []
    for i in range(6):
        col = i % cols
        row = i // cols
        x = col * col_w + 40
        y = row * row_h + 40
        positions.append((x, y))

    # Render each Pokémon
    for i, poke in enumerate(team):
        species = poke["species"]
        moves = poke["moveset"]
        sprite = fetch_gen1_sprite(species)

        x, y = positions[i]
        draw_pokemon_block(draw, canvas, x, y, species, moves, sprite, font_name, font_moves)

    canvas.save(output)
    print("Saved:", output)


# Example usage
if __name__ == "__main__":
    # Insert one of your experiment files:
    make_team_card_from_json(
        "results/experiments/ga_seed3_B10000_nb1.json",
        "ga_seed3_gen1_team.png"
    )
    make_team_card_from_json(
        "results/experiments/ga_seed1_B10000_nb1.json",
        "ga_seed1_gen1_team.png"
    )
