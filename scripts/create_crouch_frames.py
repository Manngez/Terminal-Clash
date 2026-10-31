#!/usr/bin/env python3
"""Create low defensive stances using the approved full-body sprite artwork.

No automatic masking or color removal. The fighter's original alpha, boots,
colors and outlines are preserved. The boots remain anchored to the ground.
"""
from pathlib import Path
from PIL import Image

assets = Path("assets")
for actor in ("courier", "customer"):
    source = assets / f"{actor}_idle.png"
    if not source.is_file():
        raise FileNotFoundError(source)
    image = Image.open(source).convert("RGBA")
    if image.size != (640, 620):
        raise ValueError(f"Unexpected sprite size: {source}: {image.size}")
    target = Image.new("RGBA", image.size, (0, 0, 0, 0))
    # The compressed legs form a wider, bent-knee stance. The torso remains
    # undistorted and lowers toward the knees.
    lower = image.crop((0, 332, 640, 620))
    lower = lower.resize((640, round(lower.height * 0.66)), Image.Resampling.NEAREST)
    target.alpha_composite(lower, (0, 620 - lower.height))
    upper = image.crop((0, 0, 640, 400))
    target.alpha_composite(upper, (0, 75))
    assert target.getbbox() is not None
    out = assets / f"{actor}_crouch.png"
    target.save(out, optimize=True)
    print(f"Created preserved-alpha crouch sprite: {out}, {out.stat().st_size} bytes")
