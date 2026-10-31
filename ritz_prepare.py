from pathlib import Path
from PIL import Image
import numpy as np

assets = Path("assets")
CANVAS = (180, 170)
GROUND = 162
# All animation frames use the same canvas and ground anchor.
for who in ("courier", "customer"):
    for src in sorted(assets.glob(who + "_*.png")):
        im = Image.open(src).convert("RGBA")
        a = np.array(im)
        mask = a[:, :, 3] > 0
        if not mask.any():
            raise RuntimeError("Empty sprite: " + str(src))
        # Preserve every original opaque pixel in the fighter, including dark
        # trousers and boots. Never discard disconnected components: kicks,
        # gloves and separated feet are legitimate parts of a sprite.
        # Only remove the sheet's dark navy backdrop if it connects to an
        # image edge. Flood-fill through background-colored pixels, not through
        # the character's black outlines.
        from collections import deque
        rgb = a[:, :, :3].astype(np.int16)
        h, w = a.shape[:2]
        corners = np.array([rgb[0,0], rgb[0,w-1], rgb[h-1,0], rgb[h-1,w-1]])
        bg_color = np.median(corners, axis=0)
        difference = np.max(np.abs(rgb - bg_color), axis=2)
        background_like = (difference < 39) & (a[:, :, 3] > 0)
        seen = np.zeros((h,w), dtype=bool)
        q = deque()
        for x in range(w):
            if background_like[0,x]: q.append((0,x))
            if background_like[h-1,x]: q.append((h-1,x))
        for y in range(h):
            if background_like[y,0]: q.append((y,0))
            if background_like[y,w-1]: q.append((y,w-1))
        while q:
            y,x = q.popleft()
            if seen[y,x] or not background_like[y,x]:
                continue
            seen[y,x] = True
            for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=ny<h and 0<=nx<w and not seen[ny,nx] and background_like[ny,nx]:
                    q.append((ny,nx))
        a[seen,3] = 0
        im = Image.fromarray(a)
        bbox = im.getbbox()
        if bbox is None:
            raise RuntimeError("Sprite vanished: " + str(src))
        im = im.crop(bbox)
        # Uniform height, no stretching between poses. Preserve full kick width.
        factor = min(1.0, 152 / im.height, 174 / im.width)
        if factor < 1:
            im = im.resize((max(1, round(im.width * factor)), max(1, round(im.height * factor))), Image.Resampling.NEAREST)
        dst = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
        x = (CANVAS[0] - im.width) // 2
        y = GROUND - im.height
        dst.paste(im, (x, y))
        dst.save(src)
        assert dst.getpixel((0, 0))[3] == 0
        print(src, "alpha aligned", im.size)

game = Path("game.gd")
s = game.read_text()
s = s.replace('draw_texture_rect(BG,Rect2(0,0,960,540),false)', 'draw_texture_rect(BG,Rect2(0,103,960,437),false)')
s = s.replace('var scale_factor=1.35', 'var scale_factor=1.65')
s = s.replace('var width=art.get_width()*scale_factor', 'var width=art.get_width()*scale_factor')
s = s.replace('draw_texture_rect(art,Rect2(-width/2,-height,width,height),false)', 'draw_texture_rect(art,Rect2(-width/2,-height+13,width,height),false)')
game.write_text(s)
print("Ritz background-only transparency and complete legs preserved.")
