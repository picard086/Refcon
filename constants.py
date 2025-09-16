# ---------------- Donor System ----------------

DONOR_TIERS = {
    "t1": {"slots": 3, "multiplier": 1.25, "coins": 1000, "gold": 1, "label": "Bronze"},
    "t2": {"slots": 6, "multiplier": 1.5,  "coins": 2000, "gold": 2, "label": "Silver"},
    "t3": {"slots": 9, "multiplier": 1.75, "coins": 3000, "gold": 3, "label": "Gold"},
    "t4": {"slots": 12,"multiplier": 2.0,  "coins": 4000,"gold": 4, "label": "Platinum"},
}


DONOR_PACK = [
    {"name": "qt_sarah", "amount": 1},
    {"name": "qt_taylor", "amount": 1},
    {"name": "resourceWoodBundle", "amount": 1},
    {"name": "questRewardT1SkillMagazineBundle", "amount": 2},
    {"name": "ammo9mmBulletBall", "amount": 300},
    {"name": "ammo762mmBulletBall", "amount": 300},
    {"name": "medicalFirstAidKit", "amount": 2},
]

# ---------------- Starter & Rewards ----------------

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

SOIL_REWARD = {"name": "resourceFertilizer", "friendly": "Soil", "amount": 50}

# ---------------- Vehicle Recall ----------------

VEHICLE_COMMANDS = {
    "bike": "getbike",
    "4x4": "get4x4",
    "gyro": "getgyrocopter",
    "drone": "getdrone",
}

# ---------------- Hardwired Shops ----------------

DEFAULT_SHOP = [
    {"id": 1, "name": "ammoShotgunShell", "friendly": "Stack of Shotgun Shells", "price": 250, "amount": 300},
    {"id": 2, "name": "drinkJarGrandpasLearningElixir", "friendly": "Learnin' Elixir", "price": 100, "amount": 1},
    {"id": 3, "name": "qt_taylor", "friendly": "Treasure Map", "price": 100, "amount": 1},
    {"id": 4, "name": "Cont_BooksT2", "friendly": "Useful Knowledge Quest", "price": 100, "amount": 1},
    {"id": 5, "name": "cntVendingMachine", "friendly": "Vending Machines", "price": 1000, "amount": 1},
    {"id": 6, "name": "ammo9mmBulletBall", "friendly": "500 9mm Ammo", "price": 250, "amount": 500},
    {"id": 7, "name": "medicalSplint", "friendly": "Splint", "price": 50, "amount": 1},
    {"id": 8, "name": "UniversalParts", "friendly": "Universal Parts", "price": 250, "amount": 25},
    {"id": 9, "name": "foodHoney", "friendly": "5 Jars of Honey", "price": 50, "amount": 5},
    {"id": 10, "name": "foodCanChicken", "friendly": "Can of Chicken", "price": 20, "amount": 1},
    {"id": 11, "name": "ammo762mmBulletBall", "friendly": "500 7.62 Rounds", "price": 500, "amount": 500},
    {"id": 12, "name": "drinkJarGrandpasForgettingElixir", "friendly": "Character Reset", "price": 100, "amount": 1},
    {"id": 13, "name": "drinkJarGoldenRodTea", "friendly": "Golden Rod Tea", "price": 50, "amount": 5},
    {"id": 14, "name": "foodCanShamSchematic", "friendly": "ShamRecipe", "price": 500, "amount": 1},
    {"id": 15, "name": "drugAntibiotics", "friendly": "Antibiotics", "price": 50, "amount": 1},
    {"id": 16, "name": "foodBaconAndEggs", "friendly": "Bacon and Eggs", "price": 25, "amount": 1},
    {"id": 17, "name": "resourceGlue", "friendly": "Glue", "price": 250, "amount": 100},
    {"id": 18, "name": "resourceRepairKit", "friendly": "Repair Kit", "price": 80, "amount": 1},
    {"id": 19, "name": "drinkJarPureMineralWater", "friendly": "Water Bottle", "price": 25, "amount": 2},
    {"id": 20, "name": "medicalFirstAidBandage", "friendly": "Bandages x5", "price": 25, "amount": 5},
    {"id": 21, "name": "ammoGasCan", "friendly": "Gas Can", "price": 100, "amount": 250},
    {"id": 22, "name": "terrTopSoil", "friendly": "Cheap Soil", "price": 1, "amount": 250},
]

DEFAULT_GOLDSHOP = [
    {"id": 1, "name": "meleeToolPaintToolAdmin", "friendly": "Endless Paint Brush", "price": 1, "amount": 1},
    {"id": 2, "name": "cntVendingMachine", "friendly": "Player Vending Machine", "price": 1, "amount": 1},
    {"id": 3, "name": "meleeMasterTool", "friendly": "Master Tool", "price": 3, "amount": 1},
]
