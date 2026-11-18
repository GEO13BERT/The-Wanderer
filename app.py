from flask import Flask, render_template, request, session, redirect, url_for
from engine import new_game, scavenge, fight, rest, recruit_team, resolve_event_choice, check_game_over, generate_random_event
import os
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "zombie_secret_key_5")

def add_log(msg, log_type=""):
    """Append an entry to the session log, keeping the last 30 entries."""
    log = session.get("log", [])
    state = session.get("game_state", {})
    log.append({"msg": msg, "type": log_type, "day": state.get("day", 1)})
    session["log"] = log[-30:]

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
    state = session["game_state"]
    state, msg = scavenge(state)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "scavenge"
    add_log(msg, "loot")
    return redirect(url_for("home"))

@app.route("/fight")
def route_fight():
    state = session["game_state"]
    # fight() warns once when health is low; clicking Fight again on the same day confirms it
    confirmed = session.pop("fight_confirm_day", None) == state["day"]
    state, msg = fight(state, ignore_low_health=confirmed)
    if msg == "LOW_HEALTH_WARNING":
        session["fight_confirm_day"] = state["day"]
        session["message"] = "Your health is low! Click Fight again if you really want to risk it."
        session["last_action"] = "default"
        return redirect(url_for("home"))
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "fight"
    log_type = "bad" if "died" in msg.lower() else "warn"
    add_log(msg, log_type)
    return redirect(url_for("home"))

@app.route("/rest_form", methods=["POST"])
def route_rest():
    portion = int(request.form.get("portion", 1))
    state = session["game_state"]
    state, msg = rest(state, portion)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "rest"
    add_log(msg, "good")
    return redirect(url_for("home"))

@app.route("/recruit")
def route_recruit():
    state = session["game_state"]
    state, msg = recruit_team(state)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "recruit"
    log_type = "bad" if "trap" in msg.lower() else "good"
    add_log(msg, log_type)
    return redirect(url_for("home"))

@app.route("/random_event")
def route_random_event():
    state = session["game_state"]
    state, msg = generate_random_event(state)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "mystery"
    add_log(msg, "warn")
    return redirect(url_for("home"))

@app.route("/event_choice/<choice>")
def route_event_choice(choice):
    state = session["game_state"]
    if choice.isdigit():
        choice = int(choice)
    state, msg = resolve_event_choice(state, choice)
    session["game_state"] = state
    session["message"] = msg
    session["last_action"] = "fight" if any(w in msg.lower() for w in ["attacked","fought","zombies"]) else "default"
    log_type = "bad" if any(w in msg.lower() for w in ["attacked","lost","zombies","trap"]) else "good"
    add_log(msg, log_type)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)