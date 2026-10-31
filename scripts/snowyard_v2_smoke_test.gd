extends SceneTree

# Real Godot 4.3 runtime tests: check mobile input, physics decisions,
# facing direction, snowball collisions and AI windup/throw/recovery.
func _initialize() -> void:
 call_deferred("_test")

func ok(condition:bool,reason:String) -> bool:
 if not condition:
  push_error("SNOWYARD V2 TEST FAILED: "+reason)
  quit(1)
  return false
 return true

func snow(kind:String,position:Vector2) -> Dictionary:
 return {"kind":kind,"p":position,"vx":-275.0,"phase":0.0,"life":2.0}

func _test() -> void:
 var resource:PackedScene=load("res://main.tscn")
 if not ok(resource!=null,"Main scene does not load"):return
 var g:Node=resource.instantiate()
 root.add_child(g)
 if not ok(g.get("state")=="title","No title menu"):return
 g.call("menu_tap",Vector2(480,300))
 if not ok(g.get("state")=="stage_select","No stage selection"):return
 g.call("choose_stage",1)
 if not ok(g.get("state")=="fight" and g.get("stage_id")==1,"Winter stage cannot be started"):return

 # Cowboy's unflipped original art faces LEFT; when enemy is right of player,
 # x scale must be +1. Mirror exactly when positions swap.
 g.set("p",Vector2(260,426))
 g.set("e",Vector2(700,426))
 if not ok(g.call("cowboy_sprite_x_scale")==1.0,"Cowboy looking away when standing right of courier"):return
 g.set("p",Vector2(820,426))
 if not ok(g.call("cowboy_sprite_x_scale")==-1.0,"Cowboy not turning to face courier on right"):return
 g.set("p",Vector2(260,426))

 var keys:Dictionary=g.get("keys")
 keys["crouch"]=true
 g.call("_process",0.016)
 if not ok(g.get("crouch_active"),"HUKA does not activate"):return
 var health:float=g.get("hp")
 var player:Vector2=g.get("p")
 g.call("hit_by_snowball",snow("high",player+Vector2(0,-153)))
 if not ok(is_equal_approx(g.get("hp"),health),"High snowball harms crouching player"):return
 g.call("hit_by_snowball",snow("mid",player+Vector2(0,-109)))
 if not ok(is_equal_approx(g.get("hp"),health),"Medium snowball harms crouching player"):return
 if not ok(g.get("snowballs_dodged")>=2,"Crouch dodges not counted"):return
 g.call("hit_by_snowball",snow("low",player+Vector2(0,-49)))
 if not ok(g.get("hp")<health,"Low ball incorrectly ignored when crouched"):return

 keys["crouch"]=false
 keys["block"]=true
 g.set("player_hurt",0.0)
 g.call("_process",0.016)
 health=g.get("hp")
 for kind in ["high","mid","low"]:
  g.call("hit_by_snowball",snow(kind,g.get("p")+Vector2(0,-109)))
  if not ok(is_equal_approx(g.get("hp"),health),"SKYDD failed for "+kind+" snowball"):return
 if not ok(g.get("snowballs_blocked")>=3,"Snowballs not logged as blocked"):return

 # Actual phone press inside the tiny protection area, including a thumb drag:
 # stay blocking until the finger is lifted.
 keys["block"]=false
 var press:=InputEventScreenTouch.new()
 press.index=5
 press.position=Vector2(900,430)
 press.pressed=true
 g.call("_input",press)
 if not ok(g.call("down","block"),"Touching SKYDD fails to activate it"):return
 var drag:=InputEventScreenDrag.new()
 drag.index=5
 drag.position=Vector2(902,490)
 g.call("_input",drag)
 if not ok(g.call("down","block"),"SKYDD lost when thumb slips downward"):return
 press.pressed=false
 g.call("_input",press)
 if not ok(not g.call("down","block"),"SKYDD remains active after finger lifts"):return

 # Snowballs use the same collision/defense function during frame updates.
 keys["crouch"]=true
 g.set("player_hurt",0.0)
 g.call("_process",0.016)
 health=g.get("hp")
 var active:Array=g.get("snowballs")
 active.clear()
 var position:Vector2=g.get("p")
 active.append(snow("high",position+Vector2(25,-153)))
 g.call("update_snowballs",0.016)
 if not ok(is_equal_approx(g.get("hp"),health) and active.size()==0,"Moving high projectile damages crouch"):return

 # A jumping player also evades a low snowball.
 keys["crouch"]=false
 g.set("p",Vector2(260,326))
 health=g.get("hp")
 g.call("hit_by_snowball",snow("low",Vector2(260,377)))
 if not ok(is_equal_approx(g.get("hp"),health),"Low snowball damages a successfully jumping player"):return
 g.set("p",Vector2(260,426))

 # Distinct phases of cowboy's ranged attack (telegraph -> throw -> recovery).
 active.clear()
 g.set("enemy_hurt",0.0)
 g.call("start_cowboy_throw")
 if not ok(g.get("cowboy_mode")=="throw_windup","Cowboy has no windup pose"):return
 g.call("update_cowboy_ai",0.51)
 if not ok(g.get("cowboy_mode")=="throw_release" and active.size()==1,"Cowboy does not release snowball after windup"):return
 var ball:Dictionary=active[0]
 if not ok(ball["vx"]<0.0,"Snowball thrown away from player"):return
 g.call("update_cowboy_ai",0.27)
 if not ok(g.get("cowboy_mode")=="throw_recover","Cowboy does not enter recovery pose"):return
 g.call("update_cowboy_ai",0.40)
 if not ok(g.get("cowboy_mode")=="idle","Cowboy does not recover"):return

 g.call("choose_stage",0)
 if not ok(g.get("stage_id")==0 and g.get("state")=="fight","Original terminal stage broken"):return
 print("SNOWYARD V2 TEST PASSED: facing, high/mid crouch, low hit, all blocked, thumb latch, moving projectile, jump, cowboy windup/throw/recovery, terminal stage")
 quit(0)
