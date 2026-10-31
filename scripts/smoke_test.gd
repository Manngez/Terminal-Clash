extends SceneTree

# Automated Godot 4.3 runtime smoke test, not merely an APK export check.
# Verifies actual game scene loads and menu, crouch, and pause state transitions.
func _initialize() -> void:
 call_deferred("_test_game")

func _check(ok:bool, message:String) -> bool:
 if not ok:
  push_error("GAME SMOKE TEST FAILED: "+message)
  quit(1)
  return false
 return true

func _test_game() -> void:
 var scene:PackedScene=load("res://main.tscn")
 if not _check(scene!=null,"Cannot load main scene"):
  return
 var game:Node=scene.instantiate()
 root.add_child(game)
 if not _check(game.get("state")=="title","Must open with main menu"):
  return
 game.call("menu_tap",Vector2(479,383))
 if not _check(game.get("state")=="help","Instructions button does not open help"):
  return
 game.call("menu_tap",Vector2(480,479))
 if not _check(game.get("state")=="title","Back button does not return to main menu"):
  return
 game.call("menu_tap",Vector2(480,315))
 if not _check(game.get("state")=="fight","Start match button does not work"):
  return
 var buttons:Dictionary=game.get("buttons")
 if not _check(buttons.has("crouch"),"Crouch touch button missing"):
  return
 var keys:Dictionary=game.get("keys")
 keys["crouch"]=true
 game.call("_process",0.016)
 if not _check(game.get("crouch_active")==true,"Holding crouch does not crouch"):
  return
 var before:float=game.get("p").x
 keys["right"]=true
 game.call("_process",0.016)
 if not _check(is_equal_approx(game.get("p").x,before),"Fighter moves while crouched"):
  return
 keys["right"]=false
 keys["crouch"]=false
 game.call("_process",0.016)
 if not _check(game.get("crouch_active")==false,"Crouch stays active after release"):
  return
 var touch:=InputEventScreenTouch.new()
 touch.pressed=true
 touch.position=Vector2(480,121)
 game.call("_input",touch)
 if not _check(game.get("state")=="pause","Pause touch button does not pause"):
  return
 game.call("menu_tap",Vector2(480,246))
 if not _check(game.get("state")=="fight","Resume button does not unpause"):
  return
 print("GAME SMOKE TEST PASSED: menu, help, combat, crouch, release, pause, resume")
 quit(0)
