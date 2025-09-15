DONOR_TIERS = {
    "t1": {"slots": 3, "mult": 1.25, "bonus_coins": 1000, "bonus_gold": 1},
    "t2": {"slots": 6, "mult": 1.5,  "bonus_coins": 2000, "bonus_gold": 2},
    "t3": {"slots": 9, "mult": 1.75, "bonus_coins": 3000, "bonus_gold": 3},
    "t4": {"slots": 12,"mult": 2.0,  "bonus_coins": 4000,"bonus_gold": 4},
}

DONOR_PACK = [
    {"name": "qt_sarah", "amount": 1},
    {"name": "qt_taylor", "amount": 1},
    {"name": "resourceWoodBundle", "amount": 1},
    {"name": "questRewardT1SkillMagazineBundle", "amount": 2},
    {"name": "ammo9mmBulletBall", "amount": 300},
]

STARTER_PACK = [
    {"name": "drinkJarYuccaJuice", "amount": 10},
    {"name": "foodBaconAndEggs", "amount": 10},
    {"name": "meleeWpnBladeT0BoneKnife", "amount": 1},
    {"name": "vehicleBicyclePlaceable", "amount": 1},
    {"name": "armorPrimitiveOutfit", "amount": 1},
    {"name": "gunHandgunT1Pistol", "amount": 1},
    {"name": "ammo9mmBulletBall", "amount": 300},
]

GIMME_REWARDS = [
    {"name": "qt_stephan", "friendly": "Stephan's Treasure Map", "amount": 1},
    {"name": "qt_jennifer", "friendly": "Jennifer's Treasure Map", "amount": 1},
    {"name": "resourceRepairKitImp", "friendly": "Improved Repair Kit", "amount": 1},
]


# --- Entry point ---
def main():
    print("[econ] Economy bot main loop starting...")
    # TODO: replace this with your actual startup logic:
    # connect telnet, load DB, start scheduler, etc.
    # for now it just sits in a loop
    import time
    while True:
        time.sleep(5)
        print("[econ] Bot heartbeat...")


if __name__ == "__main__":
    main()
