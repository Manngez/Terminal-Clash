#!/usr/bin/env python3
"""Make Terminal Deluxe practical to control with two thumbs on a phone.

Runs after the archive's game.gd is copied into the Android build. Fails
loudly if the archived source changes, rather than silently shipping old UI.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else "game.gd")
code = path.read_text(encoding="utf-8")

def replace_once(old, new):
    global code
    count = code.count(old)
    if count != 1:
        raise SystemExit(f"Control upgrade expected one match, got {count}: {old[:80]!r}")
    code = code.replace(old, new, 1)

replace_once(
'''var touches := {}
var keys := {}
var buttons := {
 "left":Rect2(16,452,68,68),"right":Rect2(90,452,68,68),"jump":Rect2(164,452,68,68),
 "punch":Rect2(633,452,68,68),"kick":Rect2(707,452,68,68),
 "block":Rect2(781,452,68,68),"special":Rect2(855,452,88,68)
}''',
'''var touches := {}
var touch_origins := {}
var swipe_jumped := {}
var jump_request := false
var keys := {}
# Two comfortable thumb zones: broad travel keys on the left, large attacks on
# the right. Guard and super remain accessible without competing for space.
var buttons := {
 "left":Rect2(16,421,102,104),
 "right":Rect2(124,421,102,104),
 "jump":Rect2(233,433,100,92),
 "punch":Rect2(604,416,119,109),
 "kick":Rect2(729,416,119,109),
 "block":Rect2(854,419,90,48),
 "special":Rect2(854,477,90,48)
}''')

replace_once(
'''func _input(event:InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed:
   if state != "fight":
    next_round()
   else:
    var b = button_at(event.position)
    touches[event.index] = b
    keys[b] = true
  elif touches.has(event.index):
   var old = touches[event.index]
   touches.erase(event.index)
   keys[old] = touches.values().has(old)
 elif event is InputEventScreenDrag and touches.has(event.index):
  var old = touches[event.index]
  var new = button_at(event.position)
  touches[event.index] = new
  keys[old] = touches.values().has(old)
  keys[new] = true
 elif event is InputEventKey and event.pressed and state != "fight":
  next_round()
func button_at(at:Vector2) -> String:
 for key in buttons:
  if buttons[key].has_point(at):return key
 return ""''',
'''func _input(event:InputEvent) -> void:
 if event is InputEventScreenTouch:
  if event.pressed:
   if state != "fight":
    next_round()
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
  # Keep movement active if a finger slides momentarily outside a button.
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
 elif event is InputEventKey and event.pressed and state != "fight":
  next_round()
func button_at(at:Vector2) -> String:
 # Tolerance for large thumbs; choose the nearest centre if hitboxes overlap.
 var best := ""
 var nearest := INF
 for key in buttons:
  var rect:Rect2 = buttons[key]
  if rect.grow(13).has_point(at):
   var center:Vector2 = rect.position + rect.size * 0.5
   var distance:float = at.distance_squared_to(center)
   if distance < nearest:
    nearest = distance
    best = key
 return best''')

replace_once(
''' state="fight"
func sparks''',
''' touches.clear()
 touch_origins.clear()
 swipe_jumped.clear()
 keys.clear()
 jump_request = false
 state="fight"
func sparks''')

replace_once(
''' if down("jump") and p.y>=FLOOR and player_hurt<=0:vy=-485
 vy+=1200*delta''',
''' if (jump_request or Input.is_key_pressed(KEY_W)) and p.y>=FLOOR and player_hurt<=0:
  vy=-485
  jump_request=false
 vy+=1200*delta''')

replace_once(
''' if enemy_cooldown<=0 and enemy_hurt<=0 and distance<115 and absf(p.y-e.y)<90:
  enemy_cooldown=randf_range(0.8,1.4)''',
''' if enemy_cooldown<=0 and enemy_hurt<=0 and distance<105 and absf(p.y-e.y)<90:
  enemy_cooldown=randf_range(1.15,1.7)''')

replace_once(
'''   hp-=10
   player_hurt=0.25''',
'''   hp-=8
   player_hurt=0.20''')

replace_once(
''' for name in buttons:
  var r:Rect2=buttons[name]
  draw_rect(r,Color("#28435e",0.88) if not down(name) else Color("#3d8caa",0.95))
  draw_rect(r,Color("#a9d8ed"),false,2)
  txt({"left":"<","right":">","jump":"HOPP","punch":"SLAG","kick":"SPARK","block":"SKYDD","special":"SUPER"}[name],r.position+Vector2(8,39),15)''',
''' # Touch controls are sized for thumbs and remain legible on small screens.
 for name in buttons:
  var r:Rect2=buttons[name]
  var active:bool = down(name)
  draw_rect(r,Color("#28435e",0.79) if not active else Color("#3d91ae",0.94))
  draw_rect(r,Color("#a9d8ed",0.90),false,2)
  var caption:String = {"left":"<","right":">","jump":"HOPP","punch":"SLAG","kick":"SPARK","block":"SKYDD","special":"SUPER"}[name]
  var font_size:int = 19 if name == "left" or name == "right" or name == "punch" or name == "kick" else 15
  var text_width:float = ThemeDB.fallback_font.get_string_size(caption,HORIZONTAL_ALIGNMENT_LEFT,-1,font_size).x
  txt(caption,r.position+Vector2((r.size.x-text_width)*0.5,r.size.y*0.5+font_size*0.35),font_size)
 if state == "fight" and timer > 93:
  txt("DRA UPP FOR HOPP",Vector2(25,408),13,Color("#e9f5fd",0.84))''')

path.write_text(code, encoding="utf-8")
print(f"Touch-control upgrade verified in {path} ({len(code)} chars)")
