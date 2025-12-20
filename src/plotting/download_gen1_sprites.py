import requests
from pathlib import Path
from io import BytesIO
from PIL import Image
import time

SPRITE_DIR = Path("plotting/sprites")
SPRITE_DIR.mkdir(parents=True, exist_ok=True)

POKEAPI_URL = "https://pokeapi.co/api/v2/pokemon/{}"


def download_sprite(pokemon_id: int):
    out_path = SPRITE_DIR / f"{pokemon_id}.png"
    if out_path.exists():
        return

    try:
        resp = requests.get(POKEAPI_URL.format(pokemon_id), timeout=10)
        resp.raise_for_status()
        data = resp.json()

        sprite_url = (
            data["sprites"]["versions"]
            ["generation-i"]["yellow"]["front_default"]
        )

        if sprite_url is None:
            print(f"No Yellow sprite for {pokemon_id}")
            return

        img_resp = requests.get(sprite_url, timeout=10)
        img_resp.raise_for_status()

        img = Image.open(BytesIO(img_resp.content)).convert("RGBA")
        img.save(out_path)

        print(f"Saved Yellow sprite {pokemon_id}")

    except Exception as e:
        print(f"Failed {pokemon_id}: {e}")


if __name__ == "__main__":
    for pid in range(1, 152):
        download_sprite(pid)
        time.sleep(0.1)
