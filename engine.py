import random
import datetime

UNCOMMON_ITEMS = [
    "Canned beans", "Canned soup", "Canned tuna", "Bottled water", "Energy bar",
    "Powdered milk", "Instant noodles", "Crackers", "Dried fruit", "Beef jerky",
    "Honey jar", "Peanut butter", "Protein powder", "Coffee grounds", "Salt bag",
]

COMMON_ITEMS = [
    "Bandages", "Antibiotics", "Painkillers", "Antiseptic wipes", "Medical tape",
    "Tourniquet", "Morphine vial", "Surgical gloves", "Adrenaline shot", "Suture kit",
    "Eye drops", "Vitamins", "Insulin pack", "Blood pressure meds", "First aid kit",
]

RARE_ITEMS = [
    "9mm bullets", "Shotgun shells", "Hunting knife", "Baseball bat", "Crowbar",
    "Machete", "Flare gun", "Pipe bomb parts", "Bear trap", "Crossbow bolt",
    "Pepper spray", "Taser", "Molotov cocktail parts", "Fire axe", "Sledgehammer",
]

EPIC_ITEMS = [
    "Rope", "Duct tape", "Lighter", "Matches", "Flashlight",
    "Batteries", "Multi-tool", "Hand saw", "Nails", "Hammer",
    "Wire cutters", "Padlock", "Tarp", "Sleeping bag", "Tent",
]

LEGENDARY_ITEMS = [
    "Walkie-talkie", "Hand-crank radio", "Solar charger", "Binoculars", "Night vision goggles",
    "Compass", "GPS device", "Flare", "Signal mirror", "Portable generator",
    "Leather jacket", "Steel-toed boots", "Gas mask", "Kevlar vest", "Riot helmet",
    "Thick gloves", "Rain poncho", "Thermal blanket", "Goggles", "Backpack",
]

# The Safe Zone is 10 stages away, each stage is 40 progress
SAFE_ZONE_DISTANCE = 400
STAGE_SIZE = 40
# Every 7 days a horde attacks your camp
HORDE_EVERY = 7

AMMO_ITEMS   = ["9mm bullets", "Shotgun shells", "Crossbow bolt"]
WEAPON_ITEMS = [i for i in RARE_ITEMS if i not in AMMO_ITEMS] + ["RPG", "AK-47", "GLOCK 19", "UZI", "Military technology guns"]
ARMOR_ITEMS  = ["Leather jacket", "Steel-toed boots", "Gas mask", "Kevlar vest", "Riot helmet", "Thick gloves"]
GUN_ITEMS    = ["RPG", "AK-47", "GLOCK 19", "UZI", "Military technology guns", "Flare gun"]

PERK_INFO = {
    "Scavenger":    "50% chance to find a second item when you scavenge",
    "Medic":        "Rations heal 30 instead of 20, medical items heal double",
    "Iron Mind":    "You lose half as much sanity",
    "Sharpshooter": "Fights cost half the ammo and give 50% more XP",
    "Stealthy":     "You face 30% fewer zombies in fights",
    "Leader":       "Recruiting works more often, survivors fight twice as hard in the Horde",
}

def item_rarity(item):
    """Used by the backpack to color each item."""
    if item in UNCOMMON_ITEMS:
        return "uncommon"
    if item in COMMON_ITEMS or item == "Med kit":
        return "common"
    if item in RARE_ITEMS or item in WEAPON_ITEMS:
        return "rare"
    if item in EPIC_ITEMS:
        return "epic"
    if item in LEGENDARY_ITEMS:
        return "legendary"
    return "special"

def is_usable(item):
    return item in UNCOMMON_ITEMS or item in COMMON_ITEMS or item in AMMO_ITEMS or item == "Med kit"

def use_item(state, item):
    """Food items give food, medical items heal, ammo items give ammo. Does not cost a day."""
    if item not in state['inventory']:
        return state, "You don't have that item."

    if item in UNCOMMON_ITEMS:
        state['inventory'].remove(item)
        state['food'] += 3
        return state, f"You opened the {item}. (+3 Food)"
    elif item in COMMON_ITEMS or item == "Med kit":
        heal = 15
        if item in ["First aid kit", "Med kit"]:
            heal = 30
        if "Medic" in state['perks']:
            heal *= 2
        state['inventory'].remove(item)
        state['health'] = min(100, state['health'] + heal)
        state['total_health_recoveries'] += 1
        return state, f"You used the {item}. (+{heal} Health)"
    elif item in AMMO_ITEMS:
        state['inventory'].remove(item)
        state['ammo'] += 10
        return state, f"You loaded the {item}. (+10 Ammo)"

    return state, f"You can't use the {item} right now."

def lose_sanity(state, amount):
    if "Iron Mind" in state.get('perks', []):
        amount //= 2
    state['sanity'] = max(0, state['sanity'] - amount)

def damage_per_zombie(state):
    """Weapons and armor in the backpack make every zombie hit softer. No ammo makes it worse."""
    factor = 3
    if any(item in WEAPON_ITEMS for item in state['inventory']):
        factor -= 1
    if any(item in ARMOR_ITEMS for item in state['inventory']):
        factor -= 1
    if state['ammo'] <= 0:
        factor += 2
    return max(1, factor)

def end_of_day(state):
    """Runs every time a day passes. Returns extra text for the message."""
    state['day'] += 1
    total_xp = (state['level'] - 1) * 100 + state['experience_points']
    state['highest_xp'] = max(state['highest_xp'], total_xp)
    extra = ""

    if state['food'] <= 0:
        state['health'] = max(0, state['health'] - 10)
        extra += " You are starving! (-10 Health)"

    if state['sanity'] <= 0:
        probability = random.randint(1, 100)
        if probability <= 30:
            state['health'] = max(0, state['health'] - 10)
            extra += " Your mind is breaking... you hurt yourself. (-10 Health)"

    if state['morale'] <= 20 and state['survivors'] > 1:
        probability = random.randint(1, 100)
        if probability <= 25:
            state['survivors'] -= 1
            extra += " A survivor lost hope and deserted your group."

    if state['day'] % HORDE_EVERY == 0 and state.get('active_event_id') is None and state['health'] > 0:
        state['active_event_id'] = 16
        extra += " HORDE NIGHT! A massive horde is coming for your camp. (1. Defend the camp | 2. Run)"

    return extra

def new_game():
    return {
        "health": 100,
        "food": 50,
        "ammo": 20,
        "experience_points": 0,
        "survivors": 1,
        "progress": 0,
        "day": 1,
        "inventory": [],
        "highest_xp": 0,
        "total_zombies_killed": 0,
        "total_food_eaten": 0,
        "total_health_recoveries": 0,
        "start_time": datetime.datetime.now().isoformat(),
        "morale":100,
        "sanity":100,
        "respect":0,
        "active_event_id": None,
        "weather":"Clear",
        "level":1,
        "perks":[]
        
       
    }

def scavenge(state):
    categories = [UNCOMMON_ITEMS, COMMON_ITEMS, RARE_ITEMS, EPIC_ITEMS, LEGENDARY_ITEMS]
    weights    = [50, 25, 15, 7, 3]
    pick = random.choices(categories, weights=weights, k=1)[0]
    item = random.choice(pick)
    state["inventory"].append(item)
    msg = f"You chose to scavenge... Fate gave you: {item}"

    if "Scavenger" in state['perks']:
        probability = random.randint(1, 100)
        if probability <= 50:
            bonus = random.choice(random.choices(categories, weights=weights, k=1)[0])
            state["inventory"].append(bonus)
            msg += f" and your Scavenger eye spotted: {bonus}"
    msg += "."

    state["progress"] += random.randint(3, 7)
    msg += end_of_day(state)
    return state, msg

def fight(state, ignore_low_health=False):
    if state["health"] <= 30 and not ignore_low_health:
        return state, "LOW_HEALTH_WARNING"

    # zombies get more dangerous as the days pass
    num_of_zombies = random.randint(1, 8 + state["day"] // 3)
    if "Stealthy" in state['perks']:
        num_of_zombies = max(1, int(num_of_zombies * 0.7))
    factor = damage_per_zombie(state)
    damage = factor * num_of_zombies
    state["health"] = max(0, state["health"] - damage)

    if state["health"] <= 0:
        state["health"] = 0
        return state, f"You fought {num_of_zombies} zombies and died..."

    ammo_used = num_of_zombies
    xp = 3 * num_of_zombies
    if "Sharpshooter" in state['perks']:
        ammo_used = (num_of_zombies + 1) // 2
        xp = int(xp * 1.5)
    state["ammo"] = max(0, state["ammo"] - ammo_used)
    state["experience_points"] += xp
    state["total_zombies_killed"] += num_of_zombies
    state["progress"] += random.randint(5, 15)

    msg = f"YOU HAVE DEFEATED {num_of_zombies} ZOMBIES! (-{damage} Health, -{ammo_used} Ammo, +{xp} XP)"
    msg += end_of_day(state)
    return state, msg

def rest(state, portion):
    weathers=['Clear','Clear','Clear','Clear', 'Rain', 'Fog' , 'Heatwave']
    state['weather']=random.choice(weathers)
    if state["food"] <= 0:
        return state, "You have no food left!"
    if portion > state["food"]:
        return state, "You don't have that much food!"

    heal_per_ration = 20
    if "Medic" in state['perks']:
        heal_per_ration = 30

    recovered = 0
    for f in range(portion):
        if state["health"] < 100:
            state["total_food_eaten"] += 1
            state["food"] -= 1
            before = state["health"]
            state["health"] = min(100, state["health"] + heal_per_ration)
            state["total_health_recoveries"] += 1
            recovered += state["health"] - before
        else:
            break

    state["progress"] += random.randint(1, 3)

    msg = f"You rested and recovered {recovered} health. "
    if state['weather']=='Heatwave':
        state['food']=max(0, state['food']-2)
        msg+="The weather was unbearable so you consumed extra food."
    elif state['weather']=='Fog':
        lose_sanity(state, 10)
        msg+="The fog scares you."
    elif state['weather']=='Clear':
        state['sanity'] = min(100, state['sanity'] + 5)
        state['morale'] = min(100, state['morale'] + 5)
        msg+="A quiet night. (+5 Sanity, +5 Morale)"

    msg += end_of_day(state)
    return state, msg

def recruit_team(state):
    if state['food'] < 2:
        return state, "You do not have enough food to recruit (need 2)."

    # respect makes strangers trust you, Leader makes it even easier
    chance = 50 + state['respect']
    if "Leader" in state['perks']:
        chance += 25
    chance = max(10, min(90, chance))

    probability = random.randint(1, 100)
    if probability > chance:
        state['food'] -= 2
        state['health'] = max(0, state['health'] - 10)
        return state, "It was a trap... You lost 2 food and 10 health."
    else:
        state['food'] -= 2
        state['survivors'] += 1
        state['experience_points'] += 5
        state['morale'] = min(100, state['morale'] + 5)
        return state, "Success! You found a survivor. (+1 Survivor, -2 Food, +5 Morale)"

def check_game_over(state):
    # running out of food no longer kills you instantly, you starve a little every day instead
    if state["health"] <= 0:
        return "lose"
    if state["progress"] >= SAFE_ZONE_DISTANCE:
        return "win"
    return None

def check_level_up(state):
    """At 100 XP the player levels up and picks one of 2 perks. Only when no event is running."""
    if state.get('experience_points', 0) < 100 or state.get('active_event_id') is not None:
        return None

    state['experience_points'] -= 100
    state['level'] += 1
    state['active_event_id'] = 999

    all_perks = list(PERK_INFO)
    available = [p for p in all_perks if p not in state.get('perks', [])]
    if len(available) < 2:
        state['offered_perks'] = available
    else:
        state['offered_perks'] = random.sample(available, 2)

    if not state['offered_perks']:
        state['active_event_id'] = None
        return "LEVEL UP! You have unlocked all perks!"
    elif len(state['offered_perks']) == 1:
        return f"LEVEL UP! Choose perk: 1. {state['offered_perks'][0]}"
    else:
        return f"LEVEL UP! Choose perk: 1. {state['offered_perks'][0]} | 2. {state['offered_perks'][1]}"

def generate_random_event(state):
    level_msg = check_level_up(state)
    if level_msg:
        return state, level_msg
    result = random.randint(0, 15)
    state['active_event_id'] = result
    
    if result == 0:
        return state, "You are getting raided by another group! (1. Fight Back | 2. Surrender)"
    elif result == 1:
        probability = random.randint(0, 1)
        if probability == 1:
            state['health'] //= 5
            state['active_event_id'] = None
            return state, "You found food, but it was spoiled. Health decreased."
        else:
            state['food'] += 1
            state['active_event_id'] = None
            return state, "You found safe food! (+1 Food)"
    elif result == 2:
        state['ammo'] //= 2  
        state['survivors'] //= 2
        state['food'] //= 2
        state['active_event_id'] = None
        return state, "Your base got raided by zombies! You lost 50% of your resources."
    elif result == 3:
        return state, "You meet a stranger. Trade 2 Food for 5 Ammo? (Y/N)"
    elif result == 4:
        state['progress'] += 50
        state['inventory'].append("vehicle")
        state['active_event_id'] = None
        return state, "You found a vehicle! (+50 Progress)"
    elif result==5:
        return state, "You found an abandoned building. Enter? (Y/N)"
    elif result==6:
        return state, "You hear someone screaming for help. Investigate? (Y/N)"
    
    elif result==7:
        return state, "You discovered that a recruit is stealing food and ammo. 1. Kill him 2. Let him go"
    elif result==8:
        return state, "You found a military base which is protected by landmines. Do you have the courage to raid it? Y|N"
    elif result==9:
        return state, "You found a dog, fedd him? Y|N"
    elif result==10:
        return state,"You hear a baby crying in a ruined house. Will you approach? Y|N"
    elif result==11:
       lose_sanity(state, 15)
       state['active_event_id']=None
       return state, "You found the slaughtered bodies of the traders. Your sanity decreased"
    elif result==12:
        state['sanity']=0
        state['active_event_id']=None
        if state.get('survivors',0)>0:
            killed_count=state['survivors']
            state['survivors']=0
            state['morale']=0
        return state,"You hear familiar voices.... you discover that your family has turned into zombies. You lose all hope and sanity and kill all your recruits"
    elif result==13:
        return state, "You found an abandoned hospital. Search the safe 1st floor or search the dark basement for better loot "
    elif result==14:
        if state.get('survivors',0)>0:
            return state,"One of your survivors got Bitten.Amputatate him or Kill him "
        state['active_event_id'] = None
        return state, "You found signs of a struggle, but nobody was there."
    elif result==15:
        return state,"Night is falling fast. Your visibility is low. Set up a secure camp(costs 5 food) | Keep scavenging in the night"

def resolve_event_choice(state, choice):
    event_id = state.get('active_event_id')
    msg = "Nothing happened."

    if event_id == 0:
        if choice == 2:
            state['ammo'] //= 2
            state['health'] //= 3
            state['survivors'] //= 4
            msg = "You surrendered. Lost resources but survived."
        elif choice == 1:
            state['ammo'] //= 2
            state['health'] //= 2
            state['survivors'] //= 3
            msg = "You fought back and survived, taking heavy losses."

    elif event_id == 3:
        if choice.upper() == 'Y':
            if state['food'] >= 2:
                state['food'] -= 2
                state['ammo'] += 5
                msg = "Trade successful! You got 5 Ammo."
            else:
                msg = "You don't have enough Food. The stranger leaves."
        else:
            msg = "You walked away from the trade."

    elif event_id == 5:
        if choice.upper() == "Y":
            probability = random.randint(0, 1)
            if probability == 0:
                state['health'] //= 3
                state['survivors'] //= 5
                msg = "The building was full of zombies. You got attacked!"
            else:
                state['food'] += 50
                state['inventory'].extend(["RPG", "AK-47", "GLOCK 19", "UZI"])
                state['experience_points'] += 25
                msg = "Jackpot! You found massive food and weapons!"
        else:
            msg = "You safely bypassed the building."
    elif event_id==6:
        if choice.upper()=="Y":
            probability=random.randint(0,1)
            if probability==0:
                state['health']-=20
                state['ammo']//=2
                msg="It was a trap! Raiders jumped you. Lost 20 health and half your ammo"
            else:
                state['survivors']+=1
                state['food']-=1
                state['experience_points']+=10
                state['inventory'].append("Med kit")
                msg= "They joined your group and gave you a med kit in behalf of saving them"
        else:
            msg="You ignored the scream, you can not risk it."
    elif event_id==7:
            if choice==1:
                state['morale']-=5
                state['respect']+=5
                state['ammo']//=7
                msg="You killed the thief, u gained respect from your soldiers"
            if choice==2:
                state['respect']-=5
                msg="You let him go, but at what cost. You lost respect from your soldiers"
    elif event_id==8:
        choice=choice.upper()
        if choice=="Y":
            probability=random.randint(0,100)
            if probability<=70:
                state['inventory'].append("Military technology guns")
                state['food']+=60
                state['respect']+=10
                msg="You sucesfully got into the military base and looted it"
            else:
                state['health']=0
                msg="You stepped on a mine. YOU DIED"
        else:
            msg="You choose to not raid the military base"
    elif event_id==9:
        choice=choice.upper()
        if choice=="Y":
            if state['food']>3:
                state['food']-=3
                state['inventory'].append("Dog")
                msg= "You decided to fed the dog and it joined you"
            else:
                msg="You do not have enough food"
        else:
            msg="You left the dog behind"
    elif event_id==10:
        choice=choice.upper()
        if choice=="Y":
            lose_sanity(state, 20)
            msg="It was a trap! The house was full of dead bodies. Your sanity is going insane"
            
        else:
            msg="You ignored the baby and continued exploring"
    elif event_id==13:
        if choice==1:
            state['food']+=2
            msg="You sucesfully looted the 1st floor"
        elif choice==2:
            probability=random.randint(1,100)
            if probability>50:
                state['inventory'].append("Med kit")
                state['health'] = min(100, state['health'] + 20)
                msg = "You braved the basement and found a Medical Stash"
            else:
                state['health']-=30
                state['ammo']//=2
                msg="The basement was a zombie nest"
        
    elif event_id==14:
        if choice==1:
            if "Med kit" in state['inventory']:
                state['inventory'].remove("Med kit")
                state['respect']+=10
                state['morale']+=10
                msg="You amputated his arm with the med kit. He survived."
            else:
                state['survivors']-=1
                msg="You tried to amputate his arm but you did not have a med kit"
        else:
            state['survivors']-=1
            lose_sanity(state, 10)
            state['respect']-=10
            msg="You decided to kill him..."
    elif event_id==15:
        if choice==1:
            if state['food']>=5:
                state['food']-=5
                state['health'] = min(100, state['health'] + 15)
                state['sanity'] = min(100, state['sanity'] + 15)
                msg = "You set up camp, ate well, and rested until dawn."
            else:
                state['health']-=10
                lose_sanity(state, 15)
                msg="You tried to camp but you did not have no food"
        elif choice==2:
            lose_sanity(state, 15)
            probability=random.randint(1,100)
            if probability>60:
                state['inventory'].append("Flashlight")
                state['ammo']+=30
                state['food']+=10
                msg="You managed to loot in the darkness"
            else:
                state['health']-=30
                msg="You barely survived"
                if state.get('survivors',0)>0:
                    state['survivors']=max(0, state['survivors']-2)
                    msg="Your survivors were surrounded by Zombies. Two of them got killed"
    elif event_id==16:
        if choice==1:
            num_of_zombies = random.randint(8, 14) + state['day'] // 3
            defenders = state['survivors']
            if "Leader" in state['perks']:
                defenders *= 2
            # every defender stops 4 zombies, the rest reach you
            remaining = max(0, num_of_zombies - 4 * defenders)
            damage = damage_per_zombie(state) * remaining
            state['health'] = max(0, state['health'] - damage)
            state['ammo'] = max(0, state['ammo'] - num_of_zombies)
            state['total_zombies_killed'] += num_of_zombies
            if state['health'] <= 0:
                msg = f"The horde of {num_of_zombies} zombies broke through. You died defending the camp..."
            else:
                state['experience_points'] += 4 * num_of_zombies
                state['respect'] += 10
                state['progress'] += 20
                state['morale'] = min(100, state['morale'] + 15)
                msg = f"You held the line against {num_of_zombies} zombies! (-{damage} Health, +{4 * num_of_zombies} XP, +20 Progress, +10 Respect)"
        elif choice==2:
            state['food'] = max(0, state['food'] - 5)
            state['morale'] = max(0, state['morale'] - 15)
            lose_sanity(state, 10)
            msg = "You ran into the night and left supplies behind. (-5 Food, -15 Morale)"
            if state['survivors'] > 1:
                state['survivors'] -= 1
                msg = "You ran into the night. One survivor didn't make it. (-1 Survivor, -5 Food, -15 Morale)"
    elif event_id==999:
        choice_idx=int(choice)-1
        if 0 <= choice_idx < len(state.get('offered_perks', [])):
            chosen_perk = state['offered_perks'][choice_idx]
            state['perks'].append(chosen_perk)
            state['offered_perks'] = []
            msg = f"You unlocked: {chosen_perk}!"
        else:
            return state, "Invalid perk choice"
    state['active_event_id'] = None
    return state, msg
