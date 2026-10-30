extends Node2D

const W = 960.0
const FLOOR = 426.0
const TERMINAL_ART = preload("res://assets/terminal.svg")
const COURIER_ART = preload("res://assets/courier.svg")
const RIVAL_ART = preload("res://assets/rival.svg")
var p = Vector2(255, FLOOR)
var e = Vector2(705, FLOOR)
var pv = Vector2.ZERO
var ev = Vector2.ZERO
var hp = 100
var ehp = 100
var timer = 99.0
var rounds = [0, 0]
var cooldown = 0.0
var enemy_cooldown = 0.0
var attack_time = 0.0
var enemy_attack_time = 0.0
var hit_flash = 0.0
var state = "title"
var pressed = {}
var pointers = {}
var buttons = {"left":Rect2(25,445,76,76),"right":Rect2(115,445,76,76),"jump":Rect2(210,445,76,76),"punch":Rect2(610,445,76,76),"kick":Rect2(700,445,76,76),"block":Rect2(790,445,76,76),"special":Rect2(880,445,76,76)}
var special = 0
var shots = []
var ai_clock = 0.0

func _ready():
	set_process(true)
	set_process_input(true)

func reset_round():
	p = Vector2(255,FLOOR)
	e = Vector2(705,FLOOR)
	pv = Vector2.ZERO
	ev = Vector2.ZERO
	hp = 100
	ehp = 100
	timer = 99
	cooldown = 0
	enemy_cooldown = 0
	attack_time = 0
	enemy_attack_time = 0
	shots.clear()
	special = 0
	state = "fight"

func _input(event):
	if event is InputEventScreenTouch:
		if event.pressed:
			if state != "fight":
				if state == "title" or state == "match_end":
					rounds = [0,0]
				reset_round()
			else:
				var key = button_at(event.position)
				pointers[event.index] = key
				pressed[key] = true
		else:
			if pointers.has(event.index):
				var key = pointers[event.index]
				pointers.erase(event.index)
				pressed[key] = pointers.values().has(key)
	elif event is InputEventScreenDrag:
		var key = button_at(event.position)
		if pointers.has(event.index):
			var old = pointers[event.index]
			if old != key:
				pointers[event.index] = key
				pressed[old] = pointers.values().has(old)
				pressed[key] = true
	elif event is InputEventKey:
		if event.pressed and state != "fight":
			if state == "title" or state == "match_end":
				rounds = [0,0]
			reset_round()

func button_at(pos):
	for key in buttons:
		if buttons[key].has_point(pos):
			return key
	return ""

func down(key):
	var keys = {"left":KEY_A,"right":KEY_D,"jump":KEY_W,"punch":KEY_J,"kick":KEY_K,"block":KEY_L,"special":KEY_I}
	return pressed.get(key,false) or Input.is_key_pressed(keys[key])

func _process(delta):
	if state != "fight":
		queue_redraw()
		return
	timer -= delta
	cooldown = maxf(0,cooldown-delta)
	enemy_cooldown = maxf(0,enemy_cooldown-delta)
	attack_time = maxf(0,attack_time-delta)
	enemy_attack_time = maxf(0,enemy_attack_time-delta)
	hit_flash = maxf(0,hit_flash-delta)
	var dir = float(int(down("right")) - int(down("left")))
	pv.x = dir * (90 if down("block") else 245)
	if down("jump") and p.y >= FLOOR:
		pv.y = -490
	pv.y += 1200*delta
	p += pv*delta
	p.y = minf(p.y,FLOOR)
	p.x = clampf(p.x,35,925)
	ai_clock += delta
	var dist = absf(p.x-e.x)
	var ed = signf(p.x-e.x)
	ev.x = ed * (115 if dist > 125 else -45 if dist < 67 else 0)
	if ai_clock > 1.9 and dist > 190 and e.y >= FLOOR:
		ev.y = -420
		ai_clock = 0
	ev.y += 1200*delta
	e += ev*delta
	e.y = minf(e.y,FLOOR)
	e.x = clampf(e.x,35,925)
	if p.distance_to(e) < 68:
		var mid = (p.x+e.x)*0.5
		p.x = mid + (-35 if p.x<e.x else 35)
		e.x = mid + (35 if p.x<e.x else -35)
	if cooldown <= 0 and not down("block"):
		if down("punch"):
			attack(9,105,0.29)
		elif down("kick"):
			attack(15,135,0.53)
		elif down("special") and special >= 40:
			special -= 40
			shots.append({"x":p.x,"y":p.y-75,"dir":signf(e.x-p.x)})
			cooldown = 0.65
	if enemy_cooldown <= 0 and dist < 125 and absf(p.y-e.y)<95:
		enemy_cooldown = randf_range(0.65,1.25)
		enemy_attack_time = 0.22
		if not down("block"):
			hp -= 7 if dist > 90 else 11
			hit_flash = 0.13
	for shot in shots.duplicate():
		shot.x += shot.dir*530*delta
		if absf(shot.x-e.x)<35 and absf(shot.y-(e.y-75))<50:
			ehp -= 22
			shots.erase(shot)
		elif shot.x < -20 or shot.x > 980:
			shots.erase(shot)
	if hp <= 0 or ehp <= 0 or timer <= 0:
		if hp > ehp:
			rounds[0] += 1
		elif ehp > hp:
			rounds[1] += 1
		state = "match_end" if max(rounds[0],rounds[1]) >= 2 else "round_end"
	queue_redraw()

func attack(damage, reach, cd):
	cooldown = cd
	attack_time = cd*0.7
	if absf(p.x-e.x)<reach and absf(p.y-e.y)<85:
		ehp -= damage
		special = mini(100,special+15)
		hit_flash = 0.12

func box(rect,color):
	draw_rect(rect,color)

func label(txt,pos,size=24,color=Color.WHITE):
	draw_string(ThemeDB.fallback_font,pos,txt,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func fighter(pos,blue,face,attacking,blocking=false):
	var art = COURIER_ART if blue else RIVAL_ART
	var width = 126.0
	var height = 158.0
	var origin = Vector2(pos.x-width*0.5,pos.y-height)
	var facing_right = face
	if facing_right:
		draw_texture_rect(art,Rect2(origin,Vector2(width,height)),false)
	else:
		draw_set_transform(Vector2(pos.x,pos.y-height),0,Vector2(-1,1))
		draw_texture_rect(art,Rect2(Vector2(-width*0.5,0),Vector2(width,height)),false)
		draw_set_transform(Vector2.ZERO)
	if attacking:
		var direction = 1 if facing_right else -1
		draw_arc(Vector2(pos.x+direction*60,pos.y-90),24, -1.2,1.2,12,Color("#fff0a4"),5)
	if blocking:
		draw_arc(Vector2(pos.x+(35 if facing_right else -35),pos.y-96),43,-1.1,1.1,16,Color("#8be8ff"),4)

func _draw():
	draw_texture_rect(TERMINAL_ART,Rect2(0,0,960,540),false)
	for i in range(0,960,80):
		draw_line(Vector2(i,410),Vector2(i-80,540),Color("#52515b"),2)
	draw_rect(Rect2(0,0,960,103),Color("#0b1027"))
	box(Rect2(30,26,360,23),Color("#681d31"))
	box(Rect2(30,26,360*maxf(0,hp)/100,23),Color("#e2b944"))
	box(Rect2(570,26,360,23),Color("#681d31"))
	box(Rect2(570,26,360*maxf(0,ehp)/100,23),Color("#e2b944"))
	label("PLAYER 1",Vector2(30,21),19)
	label("CPU",Vector2(868,21),19)
	label(str(ceili(timer)),Vector2(459,50),31)
	label("ROUNDS "+str(rounds[0])+" : "+str(rounds[1]),Vector2(408,83),18)
	box(Rect2(30,65,200,12),Color("#222c4a"))
	box(Rect2(30,65,special*2,12),Color("#4ccfe0"))
	fighter(p,true,e.x>p.x,attack_time>0,down("block"))
	fighter(e,false,p.x>e.x,enemy_attack_time>0)
	for shot in shots:
		draw_rect(Rect2(shot.x-13,shot.y-13,26,26),Color("#e4b26b"))
		draw_line(Vector2(shot.x-12,shot.y),Vector2(shot.x+12,shot.y),Color("#784c2c"),3)
	for key in buttons:
		var rect = buttons[key]
		draw_rect(rect,Color(0.12,0.21,0.35,0.78) if not down(key) else Color(0.4,0.65,0.82,0.92))
		draw_rect(rect,Color("#b9d9ed"),false,2)
		label(key.to_upper(),rect.position+Vector2(8,42),15)
	if hit_flash>0:
		draw_rect(Rect2(0,0,960,540),Color(1,1,1,0.13))
	if state != "fight":
		draw_rect(Rect2(165,135,630,230),Color(0.02,0.04,0.12,0.92))
		if state == "title":
			label("TERMINAL CLASH",Vector2(265,225),46,Color("#f3d06a"))
			label("TAP TO FIGHT",Vector2(373,292),27)
		elif state == "round_end":
			label("ROUND OVER",Vector2(334,225),38,Color("#f3d06a"))
			label("TAP FOR NEXT ROUND",Vector2(318,292),25)
		else:
			label("MATCH OVER",Vector2(328,225),38,Color("#f3d06a"))
			label("TAP TO PLAY AGAIN",Vector2(326,292),25)
