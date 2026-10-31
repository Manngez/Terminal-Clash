#!/usr/bin/env python3
"""Remove faulty multiple-figure/cropped cowboy frames and stabilize root anchors."""
from pathlib import Path
from PIL import Image, ImageChops, ImageFilter
import json, shutil, statistics

root=Path("assets")
manifest_path=root/"cowboy_v3_manifest.json"
manifest=json.loads(manifest_path.read_text("utf-8"))
frames=manifest["frames"]
# Visually inspected: these contain chopped heads/feet, other figures or remnants.
bad={
 "cowboy_getup_00.png","cowboy_hurt_02.png","cowboy_kick_00.png",
 "cowboy_recover_02.png","cowboy_recover_03.png",
 "cowboy_throw_low_00.png","cowboy_windup_00.png",
}
# A complete punch extension replaces the corrupted release pose with extra legs.
shutil.copyfile(root/"cowboy_punch_04.png",root/"cowboy_release_01.png")
W,H=640,620

def process(name):
 file=root/name
 im=Image.open(file).convert("RGBA")
 if im.size!=(W,H):raise RuntimeError("Bad size "+name)
 alpha=im.getchannel("A")
 core=bytearray(int(a>24) for a in alpha.tobytes())
 seen=bytearray(W*H)
 biggest=[]
 for first,visible in enumerate(core):
  if not visible or seen[first]:continue
  seen[first]=1
  stack=[first]
  component=[]
  while stack:
   i=stack.pop()
   component.append(i)
   y,x=divmod(i,W)
   for k in (i-1 if x else -1,i+1 if x<W-1 else -1,i-W if y else -1,i+W if y<H-1 else -1):
    if k>=0 and core[k] and not seen[k]:
     seen[k]=1
     stack.append(k)
  if len(component)>len(biggest):biggest=component
 if len(biggest)<12000:raise RuntimeError("Figure missing "+name)
 keep=bytearray(W*H)
 for i in biggest:keep[i]=255
 main=Image.frombytes("L",(W,H),bytes(keep)).filter(ImageFilter.MaxFilter(5))
 alpha=ImageChops.multiply(alpha,main)
 im.putalpha(alpha)
 x0,y0,x1,y1=alpha.getbbox()
 pixels=alpha.tobytes()
 xs=[]
 for y in range(int(y0+(y1-y0)*0.24),int(y0+(y1-y0)*0.58)):
  for x in range(x0,x1):
   if pixels[y*W+x]>160:xs.append(x)
 center=statistics.median(xs) if xs else (x0+x1)/2
 dx=max(-42,min(42,round(320-center)))
 dy=max(-8,min(8,round(567-y1)))
 target=Image.new("RGBA",(W,H),(0,0,0,0))
 target.alpha_composite(im,(dx,dy))
 target.save(file,optimize=True)

removed=0
for group,names in frames.items():
 good=[name for name in names if name not in bad]
 if len(good)<2:raise RuntimeError("Not enough frames "+group)
 removed+=len(names)-len(good)
 for name in good:process(name)
 frames[group]=good
count=sum(len(names) for names in frames.values())
if count!=70 or removed!=7:raise RuntimeError(f"Unexpected frame count {count} / {removed}")
manifest["quality_control"]={"version":4,"discarded":sorted(bad),"ground_y":567,"torso_x":320,"frame_count":count}
manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"COWBOY V4 ART CLEAN: {count} corrected frames, {removed} corrupt frames removed.")
