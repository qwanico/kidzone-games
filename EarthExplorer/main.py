import pygame
import math
import os
import threading
import queue
import io
import requests

pygame.init()

# ---------------- WINDOW ----------------

WIDTH = 1400
HEIGHT = 900

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Earth Explorer")

clock = pygame.time.Clock()


# ---------------- MAP CONSTANTS ----------------

TILE_SIZE = 256
MIN_ZOOM = 2
MAX_ZOOM = 19

# Esri World Imagery - free satellite tiles, no API key required.
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

CACHE_DIR = "tile_cache"

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (60, 60, 60)
PLACEHOLDER = (25, 35, 55)


# ---------------- SLIPPY MAP MATH ----------------
# Standard Web Mercator tile scheme (same as OpenStreetMap/Google Maps).
# At zoom z there are 2**z tiles across the whole world in each direction.

def lonlat_to_tile(lon, lat, zoom):

    n = 2 ** zoom

    x = (lon + 180.0) / 360.0 * n

    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n

    return x, y


def tile_to_lonlat(x, y, zoom):

    n = 2 ** zoom

    lon = x / n * 360.0 - 180.0

    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)

    return lon, lat


# ---------------- TILE LOADER ----------------
# Tiles are fetched on background threads (disk cache first, then network)
# so panning/zooming never blocks the main loop. Finished downloads are
# handed back through a queue and turned into pygame Surfaces on the main
# thread each frame.

session = requests.Session()
session.headers.update({"User-Agent": "EarthExplorer/1.0 (personal desktop app)"})

os.makedirs(CACHE_DIR, exist_ok=True)

result_queue = queue.Queue()
in_flight = set()
tiles = {}

MAX_WORKERS = 8
fetch_semaphore = threading.Semaphore(MAX_WORKERS)


def tile_cache_path(z, x, y):
    return os.path.join(CACHE_DIR, str(z), str(x), f"{y}.jpg")


def fetch_tile(z, x, y):

    with fetch_semaphore:

        path = tile_cache_path(z, x, y)

        try:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    data = f.read()

            else:
                url = TILE_URL.format(z=z, x=x, y=y)
                resp = session.get(url, timeout=8)
                resp.raise_for_status()
                data = resp.content

                os.makedirs(os.path.dirname(path), exist_ok=True)

                with open(path, "wb") as f:
                    f.write(data)

            result_queue.put((z, x, y, data))

        except Exception as e:
            result_queue.put((z, x, y, None))


def request_tile(z, x, y):

    n = 2 ** z

    # Longitude wraps around the world; latitude does not (Mercator cuts
    # off near the poles).
    x = x % n

    if y < 0 or y >= n:
        return

    key = (z, x, y)

    if key in tiles or key in in_flight:
        return

    in_flight.add(key)

    threading.Thread(target=fetch_tile, args=(z, x, y), daemon=True).start()


def drain_tile_queue():

    while True:

        try:
            z, x, y, data = result_queue.get_nowait()

        except queue.Empty:
            break

        key = (z, x, y)
        in_flight.discard(key)

        if data is None:
            tiles[key] = False
            continue

        try:
            surf = pygame.image.load(io.BytesIO(data)).convert()
            tiles[key] = surf

        except Exception:
            tiles[key] = False


# ---------------- VIEW STATE ----------------

view_lon = -98.5795
view_lat = 39.8283
zoom = 4

dragging = False
drag_last_pos = None


def clamp_zoom(z):
    return max(MIN_ZOOM, min(MAX_ZOOM, z))


# ---------------- RENDERING ----------------

FONT = pygame.font.Font(None, 28)
SMALL_FONT = pygame.font.Font(None, 22)


def draw_map():

    cx, cy = lonlat_to_tile(view_lon, view_lat, zoom)

    world_left = cx * TILE_SIZE - WIDTH / 2
    world_top = cy * TILE_SIZE - HEIGHT / 2

    first_tx = math.floor(world_left / TILE_SIZE)
    first_ty = math.floor(world_top / TILE_SIZE)

    last_tx = math.floor((world_left + WIDTH) / TILE_SIZE)
    last_ty = math.floor((world_top + HEIGHT) / TILE_SIZE)

    screen.fill(BLACK)

    for tx in range(first_tx, last_tx + 1):

        for ty in range(first_ty, last_ty + 1):

            n = 2 ** zoom
            wrapped_x = tx % n

            if ty < 0 or ty >= n:
                continue

            key = (zoom, wrapped_x, ty)

            screen_x = tx * TILE_SIZE - world_left
            screen_y = ty * TILE_SIZE - world_top

            surf = tiles.get(key)

            if surf is None:
                request_tile(zoom, wrapped_x, ty)
                pygame.draw.rect(screen, PLACEHOLDER, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

            elif surf is False:
                pygame.draw.rect(screen, GREY, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

            else:
                screen.blit(surf, (screen_x, screen_y))


def draw_hud():

    lon_text = f"{abs(view_lon):.3f}°{'E' if view_lon >= 0 else 'W'}"
    lat_text = f"{abs(view_lat):.3f}°{'N' if view_lat >= 0 else 'S'}"

    hud_text = f"{lat_text}, {lon_text}   zoom {zoom}"

    label = FONT.render(hud_text, True, WHITE)

    bg_rect = label.get_rect()
    bg_rect.topleft = (14, HEIGHT - 40)
    bg_rect.inflate_ip(20, 14)

    bg = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
    bg.fill((0, 0, 0, 150))
    screen.blit(bg, bg_rect.topleft)

    screen.blit(label, (bg_rect.x + 10, bg_rect.y + 7))

    hint = SMALL_FONT.render("Drag to pan - scroll to zoom - / to search - Esc to quit", True, WHITE)
    hint_rect = hint.get_rect()
    hint_bg = pygame.Surface((hint_rect.width + 20, hint_rect.height + 12), pygame.SRCALPHA)
    hint_bg.fill((0, 0, 0, 150))
    screen.blit(hint_bg, (14, 14))
    screen.blit(hint, (24, 20))


# ---------------- SEARCH ----------------

search_active = False
search_text = ""
search_status = ""


def geocode(query):

    global search_status

    try:
        resp = session.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
            timeout=8
        )
        resp.raise_for_status()

        results = resp.json()

        if not results:
            search_status = f'No results for "{query}"'
            return

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])

        return lon, lat

    except Exception as e:
        search_status = "Search failed - check connection"
        return


def do_search(query):

    global view_lon, view_lat, zoom, search_status

    result = geocode(query)

    if result is not None:
        view_lon, view_lat = result
        zoom = 10
        search_status = ""


def draw_search_bar():

    box = pygame.Rect(WIDTH // 2 - 260, 14, 520, 44)

    bg = pygame.Surface(box.size, pygame.SRCALPHA)
    bg.fill((20, 20, 20, 210))
    screen.blit(bg, box.topleft)

    pygame.draw.rect(screen, WHITE, box, 2, border_radius=6)

    display_text = search_text if search_text else "Type a place name, press Enter..."
    color = WHITE if search_text else (160, 160, 160)

    text_surf = FONT.render(display_text, True, color)
    screen.blit(text_surf, (box.x + 12, box.y + 10))

    if search_status:

        status_surf = SMALL_FONT.render(search_status, True, (255, 140, 140))

        status_bg = pygame.Surface((status_surf.get_width() + 16, status_surf.get_height() + 10), pygame.SRCALPHA)
        status_bg.fill((0, 0, 0, 180))
        screen.blit(status_bg, (box.x, box.bottom + 6))
        screen.blit(status_surf, (box.x + 8, box.bottom + 11))


# ---------------- MAIN LOOP ----------------

running = True

while running:

    clock.tick(60)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if search_active:

                if event.key == pygame.K_RETURN:

                    if search_text.strip():
                        threading.Thread(target=do_search, args=(search_text.strip(),), daemon=True).start()

                    search_active = False

                elif event.key == pygame.K_ESCAPE:
                    search_active = False
                    search_text = ""

                elif event.key == pygame.K_BACKSPACE:
                    search_text = search_text[:-1]

                else:
                    search_text += event.unicode

            else:

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SLASH:
                    search_active = True
                    search_text = ""
                    search_status = ""

                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    zoom = clamp_zoom(zoom + 1)

                elif event.key == pygame.K_MINUS:
                    zoom = clamp_zoom(zoom - 1)

        elif event.type == pygame.MOUSEBUTTONDOWN and not search_active:

            if event.button == 1:
                dragging = True
                drag_last_pos = event.pos

            elif event.button in (4, 5):

                # Zoom toward the cursor: keep the lon/lat under the mouse
                # fixed on screen before and after the zoom change.
                mouse_x, mouse_y = event.pos

                cx, cy = lonlat_to_tile(view_lon, view_lat, zoom)
                world_left = cx * TILE_SIZE - WIDTH / 2
                world_top = cy * TILE_SIZE - HEIGHT / 2

                target_tile_x = (world_left + mouse_x) / TILE_SIZE
                target_tile_y = (world_top + mouse_y) / TILE_SIZE
                target_lon, target_lat = tile_to_lonlat(target_tile_x, target_tile_y, zoom)

                new_zoom = clamp_zoom(zoom + (1 if event.button == 4 else -1))

                if new_zoom != zoom:

                    zoom = new_zoom

                    ncx, ncy = lonlat_to_tile(target_lon, target_lat, zoom)
                    new_world_left = ncx * TILE_SIZE - mouse_x
                    new_world_top = ncy * TILE_SIZE - mouse_y

                    center_tile_x = (new_world_left + WIDTH / 2) / TILE_SIZE
                    center_tile_y = (new_world_top + HEIGHT / 2) / TILE_SIZE

                    view_lon, view_lat = tile_to_lonlat(center_tile_x, center_tile_y, zoom)

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:
                dragging = False
                drag_last_pos = None

        elif event.type == pygame.MOUSEMOTION and dragging:

            dx = event.pos[0] - drag_last_pos[0]
            dy = event.pos[1] - drag_last_pos[1]
            drag_last_pos = event.pos

            cx, cy = lonlat_to_tile(view_lon, view_lat, zoom)
            cx -= dx / TILE_SIZE
            cy -= dy / TILE_SIZE

            n = 2 ** zoom
            cx = cx % n
            cy = max(0.0, min(n, cy))

            view_lon, view_lat = tile_to_lonlat(cx, cy, zoom)


    drain_tile_queue()

    draw_map()
    draw_hud()

    if search_active:
        draw_search_bar()

    pygame.display.update()


pygame.quit()
