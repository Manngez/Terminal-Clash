extends Node2D

const W = 960.0
const FLOOR = 426.0
const TERMINAL_ART = preload("res://assets/terminal.svg")
const COURIER_ART = preload("res://assets/courier.svg")
const RIVAL_ART = preload("res://assets/rival.svg")
const COURIER_RUN1 = preload("res://assets/courier_run1.svg")
const RIVAL_RUN1 = preload("res://assets/rival_run1.svg")
const COURIER_RUN2 = preload("res://assets/courier_run2.svg")
const RIVAL_RUN2 = preload("res://assets/rival_run2.svg")
const COURIER_PUNCH = preload("res://assets/courier_punch.svg")
const RIVAL_PUNCH = preload("res://assets/rival_punch.svg")
const COURIER_KICK = preload("res://assets/courier_kick.svg")
const RIVAL_KICK = preload("res://assets/rival_kick.svg")
const COURIER_HURT = preload("res://assets/courier_hurt.svg")
const RIVAL_HURT = preload("res://assets/rival_hurt.svg")
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
var game_clock = 0.0
var player_kick_time = 0.0
var enemy_hurt_time = 0.0
var player_hurt_time = 0.0
var impact_sparks = []
var camera_shake = 0.0

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
	player_kick_time = 0.0
	enemy_hurt_time = 0.0
	player_hurt_time = 0.0
	impact_sparks.clear()
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
	game_clock += delta
	if state != "fight":
		queue_redraw()
		return
	timer -= delta
	cooldown = maxf(0,cooldown-delta)
	enemy_cooldown = maxf(0,enemy_cooldown-delta)
	attack_time = maxf(0,attack_time-delta)
	enemy_attack_time = maxf(0,enemy_attack_time-delta)
	hit_flash = maxf(0,hit_flash-delta)
	player_kick_time = maxf(0,player_kick_time-delta)
	enemy_hurt_time = maxf(0,enemy_hurt_time-delta)
	player_hurt_time = maxf(0,player_hurt_time-delta)
	camera_shake = maxf(0,camera_shake-delta)
	for spark in impact_sparks:
		spark["life"] -= delta
		spark["pos"] += spark["velocity"]*delta
	impact_sparks = impact_sparks.filter(func(spark): return spark["life"] > 0.0)
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
			attack(9,105,0.29,false)
		elif down("kick"):
			attack(15,135,0.53,true)
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
			player_hurt_time = 0.22
			camera_shake = 0.15
			spawn_sparks(p+Vector2(0,-90),Color("#ffbf82"))
	for shot in shots.duplicate():
		shot.x += shot.dir*530*delta
		if absf(shot.x-e.x)<35 and absf(shot.y-(e.y-75))<50:
			ehp -= 22
			enemy_hurt_time = 0.25
			camera_shake = 0.19
			spawn_sparks(e+Vector2(0,-90),Color("#70eaff"))
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

func spawn_sparks(where:Vector2,tint:Color):
	for i in range(9):
		var angle = TAU*float(i)/9.0
		impact_sparks.append({"pos":where,"velocity":Vector2(cos(angle),sin(angle))*randf_range(65,190),"life":0.32,"color":tint})

func attack(damage,reach,cd,is_kick=false):
	cooldown = cd
	attack_time = cd*0.7
	if is_kick:
		player_kick_time = cd*0.7
	if absf(p.x-e.x)<reach and absf(p.y-e.y)<85:
		ehp -= damage
		special = mini(100,special+15)
		hit_flash = 0.12
		enemy_hurt_time = 0.22
		camera_shake = 0.13
		spawn_sparks(e+Vector2(0,-92),Color("#ffde84"))

func box(rect,color):
	draw_rect(rect,color)

func label(txt,pos,size=24,color=Color.WHITE):
	draw_string(ThemeDB.fallback_font,pos,txt,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func fighter(pos,blue,face,attacking,blocking=false):
	var art = COURIER_ART if blue else RIVAL_ART
	var move_frame = int(game_clock*9.0)%2
	if blue:
		if player_hurt_time>0:
			art = COURIER_HURT
		elif player_kick_time>0:
			art = COURIER_KICK
		elif attacking:
			art = COURIER_PUNCH
		elif pos.y < FLOOR-4:
			art = COURIER_RUN2
		elif absf(pv.x)>12:
			art = COURIER_RUN1 if move_frame==0 else COURIER_RUN2
	else:
		if enemy_hurt_time>0:
			art = RIVAL_HURT
		elif attacking:
			art = RIVAL_PUNCH
		elif pos.y < FLOOR-4:
			art = RIVAL_RUN2
		elif absf(ev.x)>12:
			art = RIVAL_RUN1 if move_frame==0 else RIVAL_RUN2
	var facing_right = face
	var direction = 1.0 if facing_right else -1.0
	var moving = absf(pv.x)>12 if blue else absf(ev.x)>12
	var airborne = pos.y < FLOOR-4
	var kick = blue and player_kick_time>0
	var hurt = player_hurt_time>0 if blue else enemy_hurt_time>0
	var bounce = sin(game_clock*14.0)*3.0 if moving and not airborne else 0.0
	var lean = -0.15*direction if hurt else 0.12*direction if attacking else 0.0
	var scale = Vector2(direction*(1.0 if not kick else 1.08),1.0)
	draw_set_transform(Vector2(pos.x,pos.y+bounce),lean,scale)
	draw_texture_rect(art,Rect2(-63,-158,126,158),false)
	draw_set_transform(Vector2.ZERO)
	if airborne:
		draw_arc(Vector2(pos.x,pos.y-73),38,0.4,2.7,12,Color("#d8e9f4",0.35),3)
	if attacking:
		var strike_pos = pos+Vector2(direction*(73 if kick else 62),-56 if kick else -91)
		draw_arc(strike_pos,32 if kick else 24,-1.2,1.2,12,Color("#fff0a4"),5)
		draw_line(strike_pos+Vector2(0,-19),strike_pos+Vector2(direction*20,-29),Color("#ffffff"),3)
	if blocking:
		draw_arc(Vector2(pos.x+direction*35,pos.y-96),43,-1.1,1.1,16,Color("#8be8ff"),4)
	if hurt:
		draw_rect(Rect2(pos.x-38,pos.y-153,76,151),Color(1,0.36,0.25,0.15))

func _draw():
	draw_texture_rect(TERMINAL_ART,Rect2(0,0,960,540),false)
	if camera_shake>0:
		draw_set_transform(Vector2(randf_range(-3,3),randf_range(-3,3)))
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
	draw_set_transform(Vector2.ZERO)
	for spark in impact_sparks:
		var point = spark["pos"]
		draw_circle(point,3.5*spark["life"]/0.32,spark["color"])
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
