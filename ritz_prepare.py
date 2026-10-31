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
        # Source sheet is hard-edged pixel art. Strip stray isolated pixels,
        # retaining the primary connected character and meaningful nearby details.
        from collections import deque
        h, w = mask.shape
        seen = np.zeros_like(mask)
        components = []
        for y in range(h):
            for x in range(w):
                if not mask[y, x] or seen[y, x]:
                    continue
                q = deque([(y, x)])
                seen[y, x] = True
                points = []
                while q:
                    yy, xx = q.popleft()
                    points.append((yy, xx))
                    for ny, nx in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                components.append(points)
        components.sort(key=len, reverse=True)
        # Preserve components close to the main body (e.g. a raised fist),
        # but reject disconnected text and neighboring figures.
        main = components[0]
        my = np.array([p[0] for p in main])
        mx = np.array([p[1] for p in main])
        main_box = (int(mx.min()), int(my.min()), int(mx.max()), int(my.max()))
        keep = np.zeros_like(mask)
        for comp in components:
            ys = [p[0] for p in comp]
            xs = [p[1] for p in comp]
            box = (min(xs), min(ys), max(xs), max(ys))
            near = not (box[0] > main_box[2] + 9 or box[2] < main_box[0] - 9 or box[1] > main_box[3] + 9 or box[3] < main_box[1] - 9)
            if len(comp) >= 10 and near:
                for y, x in comp:
                    keep[y, x] = True
        a[~keep, 3] = 0
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
print("Ritz sprite transparency, ground alignment and game scale fixed.")
