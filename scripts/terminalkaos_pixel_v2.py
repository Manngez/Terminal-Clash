#!/usr/bin/env python3
"""Pixel-art grade Terminalkaos and match the enemy's visual scale to the courier.
Runs after terminalkaos.zip overlay. Stages 0 and 1 remain unchanged.
"""
from pathlib import Path
from PIL import Image,ImageEnhance,ImageFilter,ImageChops
import sys

A=Path('assets')
scene=A/'terminalkaos_stage.png'
src=Image.open(scene).convert('RGB')
w,h=src.size
sm=src.resize((w//2,h//2),Image.Resampling.LANCZOS).filter(ImageFilter.SMOOTH_MORE)
recolored=sm.quantize(colors=85,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGB')
edges=sm.convert('L').filter(ImageFilter.FIND_EDGES).point(lambda a:185 if a>100 else 0)
ink=Image.blend(recolored,Image.new('RGB',recolored.size,(7,18,33)),0.63)
recolored.paste(ink,(0,0),edges)
recolored=ImageEnhance.Color(recolored).enhance(1.34)
recolored=ImageEnhance.Contrast(recolored).enhance(1.15)
shade=Image.new('RGBA',recolored.size,(7,22,55,0))
pix=shade.load()
for yy in range(shade.height):
 alpha=int(57*(1.0-yy/max(1,shade.height)))
 for xx in range(shade.width):
  pix[xx,yy]=(7,22,55,alpha)
recolored=Image.alpha_composite(recolored.convert('RGBA'),shade).convert('RGB')
recolored.resize((w,h),Image.Resampling.NEAREST).save(scene,optimize=True)
count=0
for file in sorted(A.glob('worker_*.png')):
 original=Image.open(file).convert('RGBA')
 al=original.getchannel('A').point(lambda x:0 if x<43 else min(255,round((x-43)*1.18)+43))
 sharp=original.convert('RGB').filter(ImageFilter.UnsharpMask(1.1,175,6))
 sharp=ImageEnhance.Contrast(sharp).enhance(1.20)
 sharp=ImageEnhance.Color(sharp).enhance(1.23)
 frame=sharp.resize((320,310),Image.Resampling.BOX)
 frame=frame.quantize(colors=56,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert('RGB')
 frame=frame.resize((640,620),Image.Resampling.NEAREST).convert('RGBA')
 frame.putalpha(al)
 border=ImageChops.subtract(al.filter(ImageFilter.MaxFilter(7)),al)
 back=Image.new('RGBA',(640,620),(10,20,40,0))
 back.putalpha(border)
 back.alpha_composite(frame)
 back.save(file,optimize=True)
 count+=1

f=Path(sys.argv[1] if len(sys.argv)>1 else 'game.gd')
s=f.read_text('utf-8')
old='''  var scale:float=0.48
  draw_texture_rect(worker_art(),Rect2(-640.0*scale/2.0,-570.0*scale,640.0*scale,620.0*scale),false)'''
new='''  # Worker originally appeared two-thirds the courier height.
  # Preserve bottom anchor while matching the two fighters' visual scale.
  var scale:float=0.65
  draw_texture_rect(worker_art(),Rect2(-640.0*scale/2.0,-570.0*scale,640.0*scale,620.0*scale),false)'''
if s.count(old)!=1:
 raise SystemExit('TERMINALKAOS PIXEL UPGRADE: worker draw call not uniquely found: '+str(s.count(old)))
s=s.replace(old,new)
f.write_text(s,'utf-8')
print('TERMINALKAOS V2 VISUALS INSTALLED: pixel art stage, '+str(count)+' sharpened worker poses, 35% bigger worker')
