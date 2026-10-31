#!/usr/bin/env python3
"""Pixel-grade the third stage only; preserve every other arena."""
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageChops, ImageDraw
import sys

folder=Path(sys.argv[1] if len(sys.argv)>1 else "assets")
assert (folder/"worker_idle.png").is_file()
assert (folder/"terminalkaos_stage.png").is_file()
bg=Image.open(folder/"terminalkaos_stage.png").convert("RGB")
assert bg.size==(960,540)
small=bg.resize((480,270),Image.Resampling.LANCZOS)
small=ImageEnhance.Color(small).enhance(1.29)
small=ImageEnhance.Contrast(small).enhance(1.21)
small=ImageEnhance.Sharpness(small).enhance(1.46)
small=small.quantize(colors=96,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert("RGB")
edge=small.filter(ImageFilter.GaussianBlur(0.55)).convert("L").filter(ImageFilter.FIND_EDGES)
mask=edge.point(lambda p:85 if p>43 else 0)
small=Image.composite(Image.new("RGB",small.size,(11,22,36)),small,mask)
small.resize((960,540),Image.Resampling.NEAREST).save(folder/"terminalkaos_stage.png",optimize=True)

count=0
for path in sorted(folder.glob("worker_*.png")):
 src=Image.open(path).convert("RGBA")
 assert src.size==(640,620), (path,src.size)
 bbox=src.getchannel("A").getbbox()
 assert bbox is not None
 cropped=src.crop(bbox)
 low=path.stem in ("worker_crouch","worker_pickup")
 target=360 if low else 470
 ratio=target/cropped.height
 width=max(1,round(cropped.width*ratio))
 if width>592:
  ratio=592/cropped.width;target=round(cropped.height*ratio);width=592
 art=cropped.resize((width,target),Image.Resampling.LANCZOS)
 opacity=art.getchannel("A")
 rgb=Image.new("RGB",art.size,(31,39,51))
 rgb.paste(art.convert("RGB"),mask=opacity)
 rgb=ImageEnhance.Color(rgb).enhance(1.20)
 rgb=ImageEnhance.Contrast(rgb).enhance(1.28)
 rgb=rgb.filter(ImageFilter.UnsharpMask(radius=1.8,percent=180,threshold=3))
 rgb=rgb.quantize(colors=64,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE).convert("RGB")
 grid=(max(1,width//2),max(1,target//2))
 rgb=rgb.resize(grid,Image.Resampling.BOX).resize((width,target),Image.Resampling.NEAREST)
 alpha=opacity.resize(grid,Image.Resampling.BOX).resize((width,target),Image.Resampling.NEAREST)
 px=art.load();skin=[]
 for yy in range(max(1,int(target*0.07)),max(2,int(target*0.26)),3):
  for xx in range(int(width*0.20),int(width*0.78),3):
   r,g,b,a=px[xx,yy]
   if a>190 and r>g*1.08 and g>b*1.08 and r>105 and g>70:skin.append(xx)
 face=None
 if len(skin)>35:
  skin.sort();cx=skin[len(skin)//2];cy=int(target*0.15)
  face=Image.new("RGBA",(width,target));fd=ImageDraw.Draw(face)
  for shift in (-22,8):
   fd.rounded_rectangle((cx+shift,cy-9,cx+shift+25,cy+11),radius=3,outline=(20,29,39,255),width=4)
   fd.line((cx+shift+4,cy+4,cx+shift+19,cy+4),fill=(35,40,44,180),width=2)
  fd.line((cx+2,cy-3,cx+10,cy-4),fill=(22,27,36,255),width=3)
  fd.line((cx+11,cy+15,cx+19,cy+20,cx+13,cy+22),fill=(86,56,45,240),width=3)
  fd.line((cx-7,cy+30,cx+17,cy+30),fill=(52,42,42,240),width=3)
  face.putalpha(ImageChops.multiply(face.getchannel("A"),alpha))
 alpha=alpha.point(lambda p:255 if p>=118 else 0)
 figure=rgb.convert("RGBA");figure.putalpha(alpha)
 if face is not None:figure=Image.alpha_composite(figure,face)
 canvas=Image.new("RGBA",(640,620))
 canvas.alpha_composite(figure,((640-width)//2,570-target))
 silhouette=canvas.getchannel("A")
 stroke=ImageChops.subtract(silhouette.filter(ImageFilter.MaxFilter(7)),silhouette)
 outline=Image.new("RGBA",(640,620),(15,24,35,0));outline.putalpha(stroke)
 Image.alpha_composite(outline,canvas).save(path,optimize=True)
 count+=1
assert count>=17,count
print("TERMINALKAOS V2 STYLE PASSED: 96-color pixel arena,",count,"sharpened, full-sized outlined worker sprites; stages 1 and 2 untouched")
