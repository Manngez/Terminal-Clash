#!/usr/bin/env python3
"""Add a real title/help/pause menu and meaningful crouch mechanics.

The existing Terminal Deluxe artwork and touch improvements are untouched.
Run after upgrade_touch_controls.py, before Godot imports the assets.
Every replacement is checked so a changed upstream file cannot be patched
halfway without causing CI to fail.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "game.gd")
code = path.read_text(encoding="utf-8")

def once(old: str, new: str) -> None:
    global code
    if code.count(old) != 1:
        raise SystemExit(f"Menu/crouch patch expected exactly one: {old[:120]!r}; found {code.count(old)}")
    code = code.replace(old, new, 1)

def section(start: str, end: str, new: str) -> None:
    global code
    if code.count(start) != 1 or code.count(end) != 1:
        raise SystemExit(f"Missing or duplicate code section: {start[:80]!r}, {end[:80]!r}")
    i = code.index(start)
    j = code.index(end, i+len(start))
    code = code[:i] + new + code[j:]

once(' "idle":preload("res://assets/courier_idle.png"),', ' "idle":preload("res://assets/courier_idle.png"),\n "crouch":preload("res://assets/courier_crouch.png"),')
once(' "idle":preload("res://assets/customer_idle.png"),', ' "idle":preload("res://assets/customer_idle.png"),\n "crouch":preload("res://assets/customer_crouch.png"),')
once('var message := ""', '''var message := ""
var crouch_active := false
var dodge_flash := 0.0
var pause_button := Rect2(441,109,78,29)
var title_play := Rect2(347,284,266,60)
var title_help := Rect2(347,359,266,55)
var help_back := Rect2(347,452,266,54)
var pause_resume := Rect2(346,219,268,57)
var pause_restart := Rect2(346,293,268,57)
var pause_home := Rect2(346,367,268,57)
var round_next := Rect2(346,288,268,57)
var round_home := Rect2(346,365,268,57)''')
once(' "jump":Rect2(233,433,100,92),', ' "jump":Rect2(233,433,100,92),\n "crouch":Rect2(341,433,100,92),')
once('"jump":KEY_W,"punch":KEY_J', '"jump":KEY_W,"crouch":KEY_S,"punch":KEY_J')

# Dedicated menu hit-testing: random taps outside a button do not start a game.
section('func _input(event:InputEvent) -> void:\n', 'func down(key:String) -> bool:\n', '''func clear_controls() -> void:
 touches.clear()
 touch_origins.clear()
 swipe_jumped.clear()
 keys.clear()
 jump_request = false
 crouch_active = false

func menu_tap(at:Vector2) -> void:
 match state:
  "title":
   if title_play.has_point(at):
    next_round()
   elif title_help.has_point(at):
    state = "help"
  "help":
   if help_back.has_point(at):
    state = "title"
  "pause":
   if pause_resume.has_point(at):
    state = "fight"
   elif pause_restart.has_point(at):
    player_score = 0
    enemy_score = 0
    next_round()
   elif pause_home.has_point(at):
    clear_controls()
    state = "title"
  "round_end", "match_end":
   if round_next.has_point(at):
    next_round()
   elif round_home.has_point(at):
    clear_controls()
    state = "title"
 queue_redraw()

func menu_enter() -> void:
 match state:
  "title", "round_end", "match_end":
   next_round()
  "help":
   state = "title"
  "pause":
   state = "fight"
 queue_redraw()

func _input(event:InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed:
   if state != "fight":
    menu_tap(event.position)
    return
   if pause_button.has_point(event.position):
    clear_controls()
    state = "pause"
    queue_redraw()
    return
   var b = button_at(event.position)
   if b != "":
    touches[event.index] = b
    touch_origins[event.index] = event.position
    keys[b] = true
    if b == "jump":
     jump_request = true
  elif touches.has(event.index):
   var old = touches[event.index]
   touches.erase(event.index)
   touch_origins.erase(event.index)
   swipe_jumped.erase(event.index)
   keys[old] = touches.values().has(old)
 elif event is InputEventScreenDrag and touches.has(event.index):
  var old = touches[event.index]
  if (old == "left" or old == "right") and touch_origins.has(event.index) and not swipe_jumped.has(event.index):
   if event.position.y < touch_origins[event.index].y - 52:
    jump_request = true
    swipe_jumped[event.index] = true
  var new = button_at(event.position)
  if new != "" and new != old:
   touches[event.index] = new
   keys[old] = touches.values().has(old)
   keys[new] = true
   if new == "jump":
    jump_request = true
 elif event is InputEventKey and event.pressed and not event.echo:
  if event.keycode == KEY_ESCAPE or event.keycode == KEY_P:
   if state == "fight":
    clear_controls()
    state = "pause"
   elif state == "pause":
    state = "fight"
   elif state == "help":
    state = "title"
   queue_redraw()
  elif event.keycode == KEY_ENTER or event.keycode == KEY_SPACE:
   if state != "fight":
    menu_enter()

func button_at(at:Vector2) -> String:
 var best := ""
 var nearest := INF
 for key in buttons:
  var rect:Rect2 = buttons[key]
  if rect.grow(11).has_point(at):
   var center:Vector2 = rect.position + rect.size * 0.5
   var distance:float = at.distance_squared_to(center)
   if distance < nearest:
    nearest = distance
    best = key
 return best
''')

once(' jump_request = false\n state="fight"', ' jump_request = false\n crouch_active = false\n dodge_flash = 0.0\n freeze = 0.0\n state="fight"')
once(' shake=maxf(0,shake-delta)', ' shake=maxf(0,shake-delta)\n dodge_flash=maxf(0.0,dodge_flash-delta)')
once(' var move_dir=float(int(down("right"))-int(down("left")))\n if player_hurt>0:move_dir=0', ''' crouch_active = down("crouch") and p.y >= FLOOR-2 and player_hurt <= 0
 var move_dir=float(int(down("right"))-int(down("left")))
 if player_hurt>0 or crouch_active:move_dir=0''')
once(' if (jump_request or Input.is_key_pressed(KEY_W)) and p.y>=FLOOR and player_hurt<=0:', ' if (jump_request or Input.is_key_pressed(KEY_W)) and p.y>=FLOOR and player_hurt<=0 and not crouch_active:')
once('  jump_request=false\n vy+=1200*delta', '  jump_request=false\n if crouch_active:jump_request=false\n vy+=1200*delta')
once('  if down("punch"):strike(9,112,0.34)\n  elif down("kick"):strike(15,146,0.58,true)', '''  if down("punch") and not crouch_active:
   strike(9,112,0.34)
  elif down("kick"):
   if crouch_active:
    strike(11,124,0.52,true)
   else:
    strike(15,146,0.58,true)''')
once('''  if not down("block"):
   hp-=8
   player_hurt=0.20''', '''  if crouch_active and enemy_kick_time<=0.0:
   # A crouch ducks a high punch. Low kicks still connect.
   dodge_flash=0.42
   special=minf(100,special+5)
  elif not down("block"):
   hp-=8
   player_hurt=0.20''')
once(' elif at.y<FLOOR-5:\n  key="jump"', ''' elif courier and crouch_active and state=="fight":
  key="crouch"
 elif at.y<FLOOR-5:
  key="jump"''')
once(''' if courier and down("block") and state=="fight":''', ''' if courier and crouch_active and state=="fight" and player_kick_time>0:
  var sweep_dir=1 if facing else -1
  draw_arc(at+Vector2(70*sweep_dir,-38),28,-1.25,1.25,16,Color("#ffe1a3",0.8),3.0)
 if courier and down("block") and state=="fight":''')

once('''func _draw() -> void:
 draw_texture_rect(BG,Rect2(0,0,960,540),false)''', '''func _draw() -> void:
 draw_texture_rect(BG,Rect2(0,0,960,540),false)
 if state == "title":
  draw_title_screen()
  return
 if state == "help":
  draw_help_screen()
  return''')
once(''' for name in buttons:
  var r:Rect2=buttons[name]
  var active:bool = down(name)
  draw_rect(r,Color("#28435e",0.79) if not active else Color("#3d91ae",0.94))
  draw_rect(r,Color("#a9d8ed",0.90),false,2)
  var caption:String = {"left":"<","right":">","jump":"HOPP","punch":"SLAG","kick":"SPARK","block":"SKYDD","special":"SUPER"}[name]
  var font_size:int = 19 if name == "left" or name == "right" or name == "punch" or name == "kick" else 15
  var text_width:float = ThemeDB.fallback_font.get_string_size(caption,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x
  txt(caption,r.position+Vector2((r.size.x-text_width)*0.5,r.size.y*0.5+font_size*0.35),font_size)
 if state == "fight" and timer > 93:
  txt("DRA UPP FOR HOPP",Vector2(25,408),13,Color("#e9f5fd",0.84))''', ''' if state=="fight":
  for name in buttons:
   var r:Rect2=buttons[name]
   var active:bool = down(name)
   draw_rect(r,Color("#28435e",0.79) if not active else Color("#3d91ae",0.94))
   draw_rect(r,Color("#a9d8ed",0.90),false,2)
   var caption:String = {"left":"<","right":">","jump":"HOPP","crouch":"HUKA","punch":"SLAG","kick":"SPARK","block":"SKYDD","special":"SUPER"}[name]
   var font_size:int = 19 if name == "left" or name == "right" or name == "punch" or name == "kick" else 15
   var text_width:float = ThemeDB.fallback_font.get_string_size(caption,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x
   txt(caption,r.position+Vector2((r.size.x-text_width)*0.5,r.size.y*0.5+font_size*0.35),font_size)
  draw_rect(pause_button,Color("#14263e",0.78))
  draw_rect(pause_button,Color("#9bd1ea"),false,1)
  centered_text("PAUS",pause_button.position.y+20,15,Color("#d6edfb"),pause_button)
  if timer>93:
   txt("SVE P UPP FOR HOPP".replace("SVE P","SVEP"),Vector2(23,407),12,Color("#e9f5fd",0.86))
  if dodge_flash>0:
   txt("UNDVEK!",Vector2(p.x-49,p.y-184),18,Color("#6af3e7"))''')
section(' if state!="fight":\n  draw_rect(Rect2(185,149,590,215)', 'func draw_ellipse_shadow(at:Vector2) -> void:\n', ''' if state=="pause":
  draw_pause_screen()
 elif state=="round_end" or state=="match_end":
  draw_result_screen()

func centered_text(value:String,y:float,size:int,color:Color=Color.WHITE,area:Rect2=Rect2(0,0,960,540)) -> void:
 var width:float=ThemeDB.fallback_font.get_string_size(value,HORIZONTAL_ALIGNMENT_LEFT,-1,size).x
 txt(value,Vector2(area.position.x+(area.size.x-width)*0.5,y),size,color)

func menu_button(caption:String,r:Rect2,primary:bool=false) -> void:
 var fill:Color=Color("#efc054") if primary else Color("#1b344e",0.96)
 var edge:Color=Color("#ffdf89") if primary else Color("#81bdd7")
 draw_rect(r,Color("#06101b",0.75))
 draw_rect(r.grow(-3),fill)
 draw_rect(r,edge,false,3)
 var font_size:int=25 if primary else 20
 var ink:Color=Color("#132438") if primary else Color("#f5f4e8")
 centered_text(caption,r.position.y+r.size.y*0.5+font_size*0.35,font_size,ink,r)

func draw_title_screen() -> void:
 # The same approved game art is shown on the menu, not a new placeholder.
 draw_rect(Rect2(0,0,960,540),Color("#061227",0.52))
 draw_fighter(Vector2(155,482),true)
 draw_fighter(Vector2(805,482),false)
 draw_rect(Rect2(274,0,412,540),Color("#071527",0.87))
 draw_rect(Rect2(273,0,3,540),Color("#e0b658",0.7))
 draw_rect(Rect2(685,0,3,540),Color("#e0b658",0.7))
 draw_rect(Rect2(314,69,332,3),Color("#55cde5"))
 centered_text("PAKETKRIGET",137,55,Color("#08101e"))
 centered_text("PAKETKRIGET",134,55,Color("#ffd36f"))
 centered_text("TERMINAL CLASH",177,29,Color("#63d8ff"))
 centered_text("POSTNORD  MOT  KUNDEN",223,17,Color("#e8e9de"))
 draw_rect(Rect2(334,244,292,2),Color("#e0b658",0.9))
 menu_button("STARTA MATCH",title_play,true)
 menu_button("SÅ SPELAR DU",title_help)
 centered_text("1 SPELARE  ·  ARKAD",480,17,Color("#d9e6ee"))
 centered_text("TRYCK FÖR ATT VÄLJA",506,14,Color("#aac6d5"))

func draw_help_screen() -> void:
 draw_rect(Rect2(0,0,960,540),Color("#04101f",0.87))
 draw_rect(Rect2(122,62,716,467),Color("#091a2d",0.96))
 draw_rect(Rect2(122,62,716,467),Color("#e1b85e"),false,3)
 centered_text("SÅ SPELAR DU",131,38,Color("#ffd36f"))
 centered_text("TVÅ TUMMAR · EN DUELL",168,18,Color("#6ed9ef"))
 txt("RÖRELSE",Vector2(182,216),21,Color("#ffd36f"))
 txt("VÄNSTER / HÖGER",Vector2(182,245),18)
 txt("HOPP",Vector2(182,291),21,Color("#ffd36f"))
 txt("KNAPP ELLER SVEP UPP",Vector2(182,320),17)
 txt("HUKA",Vector2(182,363),21,Color("#ffd36f"))
 txt("HÅLL INNE HUKA",Vector2(182,393),18)
 txt("ATTACK",Vector2(536,216),21,Color("#ffd36f"))
 txt("SLAG / SPARK",Vector2(536,245),18)
 txt("FÖRSVAR",Vector2(536,291),21,Color("#ffd36f"))
 txt("SKYDD / HUKA",Vector2(536,320),18)
 txt("SUPER",Vector2(536,363),21,Color("#ffd36f"))
 txt("FYLL DIN BLÅ MÄTARE",Vector2(536,393),17)
 centered_text("HUKA UNDVIKER HÖGA SLAG – INTE SPARKAR",432,16,Color("#b5e9f7"))
 menu_button("TILLBAKA",help_back)

func draw_pause_screen() -> void:
 draw_rect(Rect2(0,0,960,540),Color("#04101d",0.75))
 draw_rect(Rect2(276,135,408,330),Color("#0a1b31",0.97))
 draw_rect(Rect2(276,135,408,330),Color("#e0b658"),false,3)
 centered_text("PAUS",194,39,Color("#ffd36f"))
 menu_button("FORTSÄTT",pause_resume,true)
 menu_button("BÖRJA OM",pause_restart)
 menu_button("HUVUDMENY",pause_home)

func draw_result_screen() -> void:
 draw_rect(Rect2(0,0,960,540),Color("#061323",0.53))
 draw_rect(Rect2(274,148,412,307),Color("#0a1a2d",0.97))
 draw_rect(Rect2(274,148,412,307),Color("#e3ba65"),false,3)
 centered_text(message,224,29,Color("#ffd36f"))
 var next_label:String="SPELA IGEN" if state=="match_end" else "NÄSTA ROND"
 menu_button(next_label,round_next,true)
 menu_button("HUVUDMENY",round_home)

''')

# Verify that the sprite frames are referenced, crouch controls are present,
# and the first draw paths return before the game's HUD is rendered.
for required in ['"crouch":preload(', 'func draw_title_screen()', 'func draw_help_screen()', 'menu_button("STARTA MATCH"', '"crouch":KEY_S', 'dodge_flash=0.42']:
    if required not in code:
        raise SystemExit(f"Missing expected final feature {required!r}")
path.write_text(code, encoding="utf-8")
print(f"Crouch + title/help/pause menus installed: {path} ({len(code)} characters)")
