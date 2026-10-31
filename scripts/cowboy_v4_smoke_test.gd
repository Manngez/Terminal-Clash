extends SceneTree

func _initialize() -> void:
 call_deferred("_test")

func check(ok:bool,message:String) -> bool:
 if not ok:
  push_error("COWBOY V4 TEST FAILED: "+message)
  quit(1)
  return false
 return true

func _test() -> void:
 var scene:PackedScene=load("res://main.tscn")
 if not check(scene!=null,"Cannot load scene"):return
 var g:Node=scene.instantiate()
 root.add_child(g)
 g.call("choose_stage",1)
 if not check(g.get("stage_id")==1,"Winter arena not loaded"):return
 var frames:Dictionary=g.get("COWBOY_V3") if false else {}
 # Textures are dynamically accessible through the selection functions.
 g.set("p",Vector2(220,426))
 g.set("e",Vector2(710,426))
 g.set("enemy_hurt",0.0)
 g.set("cowboy_mode","idle")
 g.set("clock",0.01)
 var idle_first:Texture2D=g.call("cowboy_animated_texture")
 g.set("clock",0.13)
 var idle_still:Texture2D=g.call("cowboy_animated_texture")
 if not check(idle_first==idle_still,"Idle moves too fast / frames skip"):return
 g.set("clock",0.39)
 var idle_next:Texture2D=g.call("cowboy_animated_texture")
 if not check(idle_first!=idle_next,"Idle animation stopped working"):return
 g.set("cowboy_mode","walk")
 g.set("clock",1.00)
 var walk_first:Texture2D=g.call("cowboy_animated_texture")
 g.set("clock",1.09)
 var walk_still:Texture2D=g.call("cowboy_animated_texture")
 if not check(walk_first==walk_still,"Walking frames switching too quickly"):return
 g.set("clock",1.23)
 var walk_next:Texture2D=g.call("cowboy_animated_texture")
 if not check(walk_first!=walk_next,"Walking is static"):return

 # Slower, eased movement, no immediate 3+ pixel teleport on the first tick.
 g.set("cowboy_mode","idle")
 g.set("cowboy_velocity",0.0)
 g.set("cowboy_rush_time",0.0)
 g.set("cowboy_rush_cooldown",90.0)
 g.set("cowboy_dodge_cooldown",90.0)
 g.set("snowball_cooldown",90.0)
 g.set("e",Vector2(720,426))
 g.set("p",Vector2(160,426))
 g.call("update_cowboy_ai",0.016)
 var first_step:float=absf(g.get("e").x-720.0)
 if not check(first_step<0.7,"Cowboy accelerates abruptly"):return
 if not check(absf(g.get("cowboy_velocity"))<8.0,"Sudden speed burst"):return
 for i in range(80):
  g.call("update_cowboy_ai",1.0/60.0)
 var travelled:float=720.0-g.get("e").x
 if not check(travelled>15.0 and travelled<145.0,"Cowboy walking speed not moderated: "+str(travelled)):return

 # Defensive collisions remain fixed.
 g.set("p",Vector2(260,426))
 g.set("e",Vector2(720,426))
 g.set("enemy_hurt",0.0)
 var keys:Dictionary=g.get("keys")
 keys["crouch"]=true
 g.call("_process",0.016)
 var hp:float=g.get("hp")
 g.call("hit_by_snowball",{"kind":"high","p":Vector2(260,273),"vx":-270.0,"life":3.0,"phase":0.0})
 if not check(is_equal_approx(hp,g.get("hp")),"Crouch no longer avoids high ball"):return
 keys["crouch"]=false
 keys["block"]=true
 g.call("hit_by_snowball",{"kind":"low","p":Vector2(260,377),"vx":-270.0,"life":3.0,"phase":0.0})
 if not check(is_equal_approx(hp,g.get("hp")),"Shield no longer blocks snowballs"):return
 print("COWBOY V4 TEST PASSED: slower animations, state-local timing, smooth movement, crouch + shield")
 quit(0)
