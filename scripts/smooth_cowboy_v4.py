#!/usr/bin/env python3
"""Slow and smooth Cowboy V3 movement and frame transitions in the Godot game."""
from pathlib import Path
import sys
file=Path(sys.argv[1] if len(sys.argv)>1 else "game.gd")
s=file.read_text("utf-8")
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(f"Expected one match ({n}): {old[:100]!r}")
 s=s.replace(old,new,1)

once('var cowboy_throw_low:bool = false', '''var cowboy_throw_low:bool = false
var cowboy_previous_frame_group:String = ""
var cowboy_animation_epoch:float = 0.0''')
once(' cowboy_throw_low = false\n cowboy_mode = "idle"', ''' cowboy_throw_low = false
 cowboy_previous_frame_group = ""
 cowboy_animation_epoch = clock
 cowboy_mode = "idle"''')
once(' var count:int=frames.size()\n if count<=1:return 0', ''' var count:int=frames.size()
 if cowboy_previous_frame_group!=group:
  cowboy_previous_frame_group=group
  cowboy_animation_epoch=clock
 if count<=1:return 0''')
once(' var fps:float=4.0',' var fps:float=3.2')
for old,new in [('"walk":fps=10.0','"walk":fps=5.5'),('"run":fps=16.0','"run":fps=8.0'),('"jump":fps=8.0','"jump":fps=5.0'),('"crouch":fps=5.0','"crouch":fps=3.2'),('"block":fps=4.0','"block":fps=3.2'),('"win":fps=3.0','"win":fps=2.6'),('"getup":fps=6.0','"getup":fps=4.0')]:
 once(old,new)
once(' return int(clock*fps) % count',' return int(maxf(0.0,clock-cowboy_animation_epoch)*fps) % count')
# V2's artificial lean, scale/stretch and sway were layered on top of real
# animated artwork. Render the V3 cowboy flat, anchored at fixed foot level.
once('func draw_fighter(at:Vector2,courier:bool) -> void:\n var art:Texture2D=fighter_art(courier)', '''func draw_fighter(at:Vector2,courier:bool) -> void:
 if not courier and stage_id==1:
  var sprite:Texture2D=cowboy_animated_texture()
  draw_set_transform(at,0.0,Vector2(cowboy_v3_sprite_scale(),1.0))
  var size:float=0.48
  draw_texture_rect(sprite,Rect2(-640.0*size*0.5,-570.0*size,640.0*size,620.0*size),false)
  draw_set_transform(Vector2.ZERO)
  if cowboy_mode=="throw_windup" and state=="fight":
   var facing:float=1.0 if p.x>e.x else -1.0
   var snow_point:Vector2=at+Vector2(facing*44.0,-170.0)
   draw_circle(snow_point,10.0,Color("#f0faff",0.95))
  return
 var art:Texture2D=fighter_art(courier)''')
# Stop resetting speed to zero every tick. Accelerate and decelerate gently.
once(' cowboy_velocity = 0.0\n cowboy_dodge_cooldown = maxf',' var desired_velocity:float = 0.0\n cowboy_dodge_cooldown = maxf')
once('  cowboy_mode="hurt"\n  cowboy_mode_time=0.0','  cowboy_velocity=0.0\n  cowboy_mode="hurt"\n  cowboy_mode_time=0.0')
once(' if cowboy_rush_time>0.0:\n  cowboy_velocity=toward*185.0\n elif distance>335.0:\n  cowboy_velocity=toward*150.0\n elif distance<180.0:\n  cowboy_velocity=-toward*142.0\n if absf(cowboy_velocity)>0.01:', ''' if cowboy_rush_time>0.0:
  desired_velocity=toward*115.0
 elif distance>335.0:
  desired_velocity=toward*90.0
 elif distance<180.0:
  desired_velocity=-toward*65.0
 cowboy_velocity=move_toward(cowboy_velocity,desired_velocity,delta*380.0)
 if absf(cowboy_velocity)>5.0:''')
once('cowboy_rush_time=randf_range(0.85,1.25)','cowboy_rush_time=randf_range(0.65,0.95)')
once('cowboy_rush_cooldown=randf_range(3.5,5.0)','cowboy_rush_cooldown=randf_range(4.3,6.1)')
file.write_text(s,"utf-8")
print("COWBOY V4 SMOOTHED: slower walking/running, eased acceleration, state-local frames, removed fake lean")
