#!/usr/bin/env python3
"""Correct Snowyard combat, cowboy facing and animation state machine.

Applied to the archived game.gd *inside* the GitHub Android workflow. All
edits are validated: fail the build if the game source no longer matches.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "game.gd")
s = path.read_text(encoding="utf-8")

def once(old, new):
    global s
    count=s.count(old)
    if count != 1:
        raise SystemExit("Expected exactly one match (%s), found %d" % (old[:75],count))
    s=s.replace(old,new,1)

def block(start,end,body):
    global s
    if s.count(start)!=1 or s.count(end)!=1:
        raise SystemExit("Block not unique: "+start)
    a=s.index(start)
    b=s.index(end,a+len(start))
    s=s[:a]+body+"\n"+s[b:]

once('var snowball_cooldown:float = 1.2', '''var snowball_cooldown:float = 1.2
# Cowboy AI: windup -> release -> recovery, with movement, ducking and jumps.
var cowboy_mode:String = "idle"
var cowboy_mode_time:float = 0.0
var cowboy_velocity:float = 0.0
var cowboy_rush_time:float = 0.0
var cowboy_rush_cooldown:float = 3.8
var cowboy_dodge_cooldown:float = 1.7
var defense_message:String = ""
var defense_message_time:float = 0.0
var snowballs_blocked:int = 0
var snowballs_dodged:int = 0
var snowballs_hit:int = 0''')

once(' "block":Rect2(854,419,90,48),\n "special":Rect2(854,477,90,48)',
     ' "block":Rect2(854,410,90,58),\n "special":Rect2(854,476,90,49)')

once('''  var new_button:String = button_at(event.position)
  if new_button != "" and new_button != old_button:''','''  # Latch defensive buttons while the thumb is down, even if it slips.
  if old_button == "block" or old_button == "crouch":
   return
  var new_button:String = button_at(event.position)
  if new_button != "" and new_button != old_button:''')

once(' snowball_cooldown = 1.45', ''' snowball_cooldown = 1.45
 cowboy_mode = "idle"
 cowboy_mode_time = 0.0
 cowboy_velocity = 0.0
 cowboy_rush_time = 0.0
 cowboy_rush_cooldown = 3.8
 cowboy_dodge_cooldown = 1.7
 defense_message = ""
 defense_message_time = 0.0
 snowballs_blocked = 0
 snowballs_dodged = 0
 snowballs_hit = 0''')

block('func enemy_snow_throw() -> void:\n','func _process(delta:float) -> void:\n', '''func cowboy_faces_right() -> bool:
 # All cowboy sprite sheets naturally face LEFT (extended arm to left).
 return p.x >= e.x

func cowboy_sprite_x_scale() -> float:
 # Positive texture X is the untouched, left-facing sheet.
 return -1.0 if cowboy_faces_right() else 1.0

func start_cowboy_throw() -> void:
 cowboy_mode = "throw_windup"
 cowboy_mode_time = 0.50
 cowboy_velocity = 0.0
 enemy_throw_time = 0.0

func update_cowboy_ai(delta:float) -> void:
 if stage_id != 1:
  return
 cowboy_velocity = 0.0
 cowboy_dodge_cooldown = maxf(0.0,cowboy_dodge_cooldown-delta)
 cowboy_rush_cooldown = maxf(0.0,cowboy_rush_cooldown-delta)
 var distance:float = absf(p.x-e.x)
 var toward:float = signf(p.x-e.x)
 if toward==0.0: toward=-1.0
 if enemy_hurt>0.0:
  cowboy_mode="hurt"
  cowboy_mode_time=0.0
  enemy_throw_time=0.0
  return
 if cowboy_mode=="hurt":
  cowboy_mode="idle"
 if cowboy_mode=="throw_windup" or cowboy_mode=="throw_release" or cowboy_mode=="throw_recover":
  cowboy_mode_time=maxf(0.0,cowboy_mode_time-delta)
  if cowboy_mode_time<=0.0:
   if cowboy_mode=="throw_windup":
    enemy_snow_throw()
    cowboy_mode="throw_release"
    cowboy_mode_time=0.26
   elif cowboy_mode=="throw_release":
    cowboy_mode="throw_recover"
    cowboy_mode_time=0.36
   else:
    cowboy_mode="idle"
  return
 if cowboy_mode=="dodge":
  cowboy_mode_time=maxf(0.0,cowboy_mode_time-delta)
  if cowboy_mode_time<=0.0:cowboy_mode="idle"
  return
 if enemy_attack_time>0.0:
  cowboy_mode="kick" if enemy_kick_time>0.0 else "punch"
  return
 if cowboy_mode=="kick" or cowboy_mode=="punch":
  cowboy_mode="idle"
 if cowboy_rush_time>0.0:
  cowboy_rush_time=maxf(0.0,cowboy_rush_time-delta)
 if cowboy_dodge_cooldown<=0.0 and projectiles.size()>0 and e.y>=FLOOR:
  # Sidestep/leap over an approaching PostNord super attack.
  for shot in projectiles:
   if absf(shot["p"].x-e.x)<170.0:
    evy=-360.0
    cowboy_mode="dodge"
    cowboy_mode_time=0.32
    cowboy_dodge_cooldown=randf_range(2.2,3.6)
    return
 if cowboy_rush_cooldown<=0.0 and distance>160.0:
  cowboy_rush_time=randf_range(0.85,1.25)
  cowboy_rush_cooldown=randf_range(3.5,5.0)
 if cowboy_rush_time>0.0:
  cowboy_velocity=toward*185.0
 elif distance>335.0:
  cowboy_velocity=toward*150.0
 elif distance<180.0:
  cowboy_velocity=-toward*142.0
 if absf(cowboy_velocity)>0.01:
  cowboy_mode="walk"
  e.x=clampf(e.x+cowboy_velocity*delta,48.0,912.0)
 else:
  cowboy_mode="idle"
 # Throw from a distance with anticipation and visible recovery.
 snowball_cooldown-=delta
 if snowball_cooldown<=0.0 and distance>130.0:
  start_cowboy_throw()
  snowball_cooldown=randf_range(1.55,2.55)

func enemy_snow_throw() -> void:
 if enemy_hurt>0 or stage_id!=1:return
 var style:float=randf()
 var kind:String="high" if style<0.46 else "mid" if style<0.80 else "low"
 var offset_y:float=-153.0 if kind=="high" else -109.0 if kind=="mid" else -49.0
 var direction:float=signf(p.x-e.x)
 if direction==0.0:direction=-1.0
 var origin:Vector2=e+Vector2(direction*81.0,offset_y)
 snowballs.append({"p":origin,"vx":direction*randf_range(250.0,325.0),"kind":kind,"phase":randf_range(0.0,3.0),"life":4.0})
 enemy_throw_time=0.28
 sparks(origin,Color("#bce9ff"),7)

func snowball_defense(ball:Dictionary) -> String:
 # This is the *single source of truth* for projectile damage.
 # Block absorbs EVERY snowball, irrespective of projectile height.
 if down("block"):
  return "block"
 var crouched:bool=down("crouch") and p.y>=FLOOR-3.0
 var high_ball:bool=ball["kind"]=="high" or ball["kind"]=="mid"
 if crouched and high_ball:
  return "duck"
 if ball["kind"]=="low" and p.y<FLOOR-62.0:
  return "jump"
 # A hit requires an overlap with the fighter's actual vertical body area.
 var top_y:float=p.y-(78.0 if crouched else 192.0)
 var bottom_y:float=p.y-24.0
 var ball_y:float=ball["p"].y
 if ball_y+20.0<top_y or ball_y-20.0>bottom_y:
  return "miss"
 return "hit"

func hit_by_snowball(ball:Dictionary) -> void:
 var result:String=snowball_defense(ball)
 if result=="block":
  snowballs_blocked+=1
  defense_message="BLOCKERAD!"
  defense_message_time=0.53
  special=minf(100.0,special+5.0)
  sparks(ball["p"],Color("#65eaff"),14)
 elif result=="duck" or result=="jump" or result=="miss":
  snowballs_dodged+=1
  defense_message="DUCKAD!" if result=="duck" else "UNDVIKEN!"
  defense_message_time=0.43
  dodge_flash=0.43
  special=minf(100.0,special+3.0)
  sparks(ball["p"],Color("#a7efff"),7)
 else:
  snowballs_hit+=1
  hp=maxf(0.0,hp-(9.0 if ball["kind"]=="low" else 7.0))
  player_hurt=0.22
  p.x=clampf(p.x+signf(p.x-e.x)*16.0,50.0,910.0)
  shake=0.14
  freeze=0.04
  defense_message="TRÄFF!"
  defense_message_time=0.33
  sparks(ball["p"],Color("#fff4fb"),15)

func update_snowballs(delta:float) -> void:
 for ball in snowballs.duplicate():
  ball["p"]+=Vector2(ball["vx"]*delta,0.0)
  ball["life"]-=delta
  if absf(ball["p"].x-p.x)<38.0:
   hit_by_snowball(ball)
   snowballs.erase(ball)
  elif ball["life"]<=0.0 or ball["p"].x<-36.0 or ball["p"].x>996.0:
   snowballs.erase(ball)
''')

once(' dodge_flash = maxf(0.0,dodge_flash-delta)', ''' dodge_flash = maxf(0.0,dodge_flash-delta)
 defense_message_time=maxf(0.0,defense_message_time-delta)''')

block(' var distance:float = absf(p.x-e.x)\n if enemy_hurt<=0:\n',' evy += 1200*delta\n', ''' var distance:float = absf(p.x-e.x)
 if stage_id==1:
  update_cowboy_ai(delta)
 elif enemy_hurt<=0:
  var toward_player:float=signf(p.x-e.x)
  var enemy_direction:float=0.0
  if distance>125.0:enemy_direction=toward_player
  elif distance<70.0:enemy_direction=-toward_player
  e.x=clampf(e.x+enemy_direction*112.0*delta,48.0,912.0)
''')

once(''' if stage_id==1:
  snowball_cooldown -= delta
  if snowball_cooldown<=0 and enemy_hurt<=0:
   enemy_snow_throw()
   snowball_cooldown=randf_range(1.45,2.30)
  update_snowballs(delta)''',''' if stage_id==1:
  update_snowballs(delta)''')

# The cowboy's walk/throw/crouch/kick/jump have distinct texture selections.
block('func fighter_art(courier:bool) -> Texture2D:\n','func draw_fighter(at:Vector2,courier:bool) -> void:\n', '''func fighter_art(courier:bool) -> Texture2D:
 var library:Dictionary=COURIER if courier else (COWBOY if stage_id==1 else CUSTOMER)
 var hurt:float=player_hurt if courier else enemy_hurt
 var attack:float=attack_time if courier else enemy_attack_time
 var kick:bool=player_kick_time>0.0 if courier else enemy_kick_time>0.0
 var pose:String="idle"
 if hurt>0.0:
  pose="hurt"
 elif state=="match_end" and ((courier and player_score>enemy_score) or (not courier and enemy_score>player_score)):
  pose="win"
 elif not courier and stage_id==1:
  match cowboy_mode:
   "throw_windup":
    pose="crouch"
   "throw_release":
    pose="throw"
   "throw_recover":
    pose="idle"
   "punch":
    pose="punch1"
   "kick":
    pose="kick"
   "dodge":
    pose="jump" if e.y<FLOOR-5.0 else "crouch"
   "walk":
    pose="walk1" if int(clock*10.0)%2==0 else "walk2"
   _:
    pose="jump" if e.y<FLOOR-5.0 else "idle"
 elif attack>0.0:
  pose="kick" if kick else "punch1"
 elif courier and crouch_active and state=="fight":
  pose="crouch"
 elif (p.y if courier else e.y)<FLOOR-5.0:
  pose="jump"
 elif courier and (down("left") or down("right")) and state=="fight":
  pose="walk1" if int(clock*10.0)%2==0 else "walk2"
 elif not courier and absf(p.x-e.x)>125.0 and state=="fight":
  pose="walk1" if int(clock*9.0)%2==0 else "walk2"
 return library[pose]
''')

block('func draw_fighter(at:Vector2,courier:bool) -> void:\n','func draw_shadow(at:Vector2) -> void:\n', '''func draw_fighter(at:Vector2,courier:bool) -> void:
 var art:Texture2D=fighter_art(courier)
 var rightward:bool=e.x>p.x if courier else p.x>e.x
 # The original cowboy sprite is LEFT-facing, unlike the courier.
 var scale_x:float=(1.0 if rightward else -1.0) if (courier or stage_id==0) else cowboy_sprite_x_scale()
 var scale_y:float=1.0
 var offset:Vector2=Vector2.ZERO
 var lean:float=0.0
 if not courier and stage_id==1 and state=="fight":
  match cowboy_mode:
   "walk":
    offset.y=sin(clock*24.0)*3.2
    lean=0.018 if cowboy_velocity>0.0 else -0.018
   "throw_windup":
    scale_y=0.94
    offset.y=4.0
    lean=0.045
   "throw_release":
    scale_x*=1.04
    lean=-0.07
    offset.x=(18.0 if rightward else -18.0)
   "throw_recover":
    lean=0.025*sin(clock*14.0)
   "punch":
    offset.x=(12.0 if rightward else -12.0)
    lean=-0.045
   "kick":
    lean=0.055
   "hurt":
    lean=-0.08
   "dodge":
    offset.y=4.0
    scale_y=0.94
 draw_set_transform(at+offset,lean,Vector2(scale_x,scale_y))
 var scaled:float=0.48
 draw_texture_rect(art,Rect2(-640.0*scaled/2.0,-570.0*scaled,640.0*scaled,620.0*scaled),false)
 draw_set_transform(Vector2.ZERO)
 if not courier and stage_id==1 and cowboy_mode=="throw_windup" and state=="fight":
  var facing:float=1.0 if rightward else -1.0
  var snow_point:Vector2=at+Vector2(facing*45.0,-170.0)
  draw_circle(snow_point,11.0+2.0*sin(clock*15.0),Color("#e8faff",0.94))
  draw_arc(snow_point,17.0,0.0,TAU,20,Color("#79d9ff",0.8),2.0)
 if courier and down("block") and state=="fight":
  draw_arc(at+Vector2((40.0 if rightward else -40.0),-125.0),43,-1.1,1.1,22,Color("#96e9ff",0.86),4)
''')

once(''' if dodge_flash>0:
  txt("DUCK!",Vector2(p.x-26,p.y-186),21,Color("#8befff"))''',''' if defense_message_time>0.0 and state=="fight":
  var tone:Color=Color("#fce6b1") if defense_message=="TRÄFF!" else Color("#8befff")
  var text_width:float=ThemeDB.fallback_font.get_string_size(defense_message,HORIZONTAL_ALIGNMENT_LEFT,-1,21).x
  txt(defense_message,Vector2(p.x-text_width*0.5,p.y-195),21,tone)''')

# Explicitly teach the three projectile rules, consistent with the gameplay.
once(' txt("SNÖGÅRDEN: DUCKA FÖR HÖGA SNÖBOLLAR",Vector2(149,385),18,Color("#8fdefb"))\n txt("HOPPA ÖVER DE LÅGA!",Vector2(149,413),18,Color("#8fdefb"))',
''' txt("SNÖGÅRDEN: HUKA UNDER HÖGA & MEDELHÖGA",Vector2(149,385),17,Color("#8fdefb"))
 txt("HOPPA ÖVER LÅGA · SKYDD STOPPAR ALLA",Vector2(149,413),17,Color("#8fdefb"))''')

path.write_text(s,encoding="utf-8")
print("SNOWYARD V2 PATCH INSTALLED:",len(s),"chars")
