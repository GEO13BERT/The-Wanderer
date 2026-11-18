from flask import Flask, render_template, request, session, redirect, url_for
from engine import new_game, scavenge, fight, rest, recruit_team, resolve_event_choice, check_game_over, generate_random_event
from engine import use_item, check_level_up, item_rarity, is_usable, damage_per_zombie, PERK_INFO, STAGE_SIZE, SAFE_ZONE_DISTANCE, HORDE_EVERY
import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "zombie_secret_key_5")

# let index.html use these directly
app.jinja_env.globals.update(
    item_rarity=item_rarity, is_usable=is_usable, damage_per_zombie=damage_per_zombie,
    PERK_INFO=PERK_INFO, STAGE_SIZE=STAGE_SIZE, SAFE_ZONE_DISTANCE=SAFE_ZONE_DISTANCE, HORDE_EVERY=HORDE_EVERY,
)

def add_log(msg, log_type=""):
    """Append an entry to the session log, keeping the last 30 entries."""
    log = session.get("log", [])
    state = session.get("game_state", {})
    log.append({"msg": msg, "type": log_type, "day": state.get("day", 1)})
    session["log"] = log[-30:]

def game_running():
    """False if there is no game yet or the game is already over."""
    if "game_state" not in session:
        return False
    return check_game_over(session["game_state"]) is None

def after_action(state, msg):
    """Runs after every action: level up when XP reaches 100, and remember the event text."""
    if check_game_over(state) is None:
        level_msg = check_level_up(state)
        if level_msg:
            msg += " " + level_msg
    if state.get("active_event_id") is not None:
        state["event_text"] = msg
    return msg

@app.route("/")
def home():
    if "game_state" not in session:
        session["game_state"] = new_game()
        session["log"] = []

    state       = session["game_state"]
    msg         = session.pop("message", "")
    last_action = session.pop("last_action", "default")

    status = check_game_over(state)
    if status == "lose":
        msg = "YOU DIED! GAME OVER"
    elif status == "win":
        msg = "YOU REACHED THE SAFE ZONE!"

    return render_template("index.html", state=state, message=msg, last_action=last_action)

@app.route("/new_game")
def route_new_game():
    session.clear()
    session["game_state"] = new_game()
    session["log"] = []
    session["message"] = "A new game begins. Survive."
    return redirect(url_for("home"))

@app.route("/scavenge")
def route_scavenge():
    if not game_running():
        return redirect(url_for("home"))
    state = session["game_state"]
    state, msg = scavenge(state)
    msg = after_action(state, msg)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "scavenge"
    add_log(msg, "loot")
    return redirect(url_for("home"))

@app.route("/fight")
def route_fight():
    if not game_running():
        return redirect(url_for("home"))
    state = session["game_state"]
    # fight() warns once when health is low; clicking Fight again on the same day confirms it
    confirmed = session.pop("fight_confirm_day", None) == state["day"]
    state, msg = fight(state, ignore_low_health=confirmed)
    if msg == "LOW_HEALTH_WARNING":
        session["fight_confirm_day"] = state["day"]
        session["message"] = "Your health is low! Click Fight again if you really want to risk it."
        session["last_action"] = "default"
        return redirect(url_for("home"))
    msg = after_action(state, msg)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "fight"
    log_type = "bad" if "died" in msg.lower() or "horde" in msg.lower() else "warn"
    add_log(msg, log_type)
    return redirect(url_for("home"))

@app.route("/rest_form", methods=["POST"])
def route_rest():
    if not game_running():
        return redirect(url_for("home"))
    portion = int(request.form.get("portion", 1))
    state = session["game_state"]
    state, msg = rest(state, portion)
    msg = after_action(state, msg)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "rest"
    add_log(msg, "good")
    return redirect(url_for("home"))

@app.route("/recruit")
def route_recruit():
    if not game_running():
        return redirect(url_for("home"))
    state = session["game_state"]
    state, msg = recruit_team(state)
    msg = after_action(state, msg)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "recruit"
    log_type = "bad" if "trap" in msg.lower() else "good"
    add_log(msg, log_type)
    return redirect(url_for("home"))

@app.route("/random_event")
def route_random_event():
    if not game_running():
        return redirect(url_for("home"))
    state = session["game_state"]
    state, msg = generate_random_event(state)
    msg = after_action(state, msg)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "mystery"
    add_log(msg, "warn")
    return redirect(url_for("home"))

@app.route("/event_choice/<choice>")
def route_event_choice(choice):
    if not game_running():
        return redirect(url_for("home"))
    state = session["game_state"]
    if choice.isdigit():
        choice = int(choice)
    state, msg = resolve_event_choice(state, choice)
    msg = after_action(state, msg)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "fight" if any(w in msg.lower() for w in ["attacked","fought","zombies"]) else "default"
    log_type = "bad" if any(w in msg.lower() for w in ["attacked","lost","zombies","trap"]) else "good"
    add_log(msg, log_type)
    return redirect(url_for("home"))

@app.route("/use/<item>")
def route_use_item(item):
    if not game_running():
        return redirect(url_for("home"))
    state = session["game_state"]
    state, msg = use_item(state, item)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "default"
    add_log(msg, "good")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)