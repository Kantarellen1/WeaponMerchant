from merchants.inventory import purchase_from_merchant, MerchantInventory
from auction_house.auction_data import load_player_inventories, save_player_inventories, load_player_data, save_player_data, create_listing, buy_auction_listing

PLAYER_ID = "player_test"

# Initialize test player data
pdata = load_player_data()
pdata[PLAYER_ID] = {"gold": 200}
save_player_data(pdata)

# Clear player inventories
pinv = load_player_inventories()
pinv[PLAYER_ID] = []
save_player_inventories(pinv)

print("=== Before purchase ===")
print("Player gold:", pdata[PLAYER_ID]["gold"])
print("Player inventory:", pinv.get(PLAYER_ID))

# Purchase 1 Healing potion from elara
ok, res = purchase_from_merchant(PLAYER_ID, "elara", "healing_potion", quantity=1)
print("Purchase from merchant elara ->", ok, res)

pdata = load_player_data()
pinv = load_player_inventories()
print("=== After merchant purchase ===")
print("Player gold:", pdata[PLAYER_ID]["gold"])
print("Player inventory:", pinv.get(PLAYER_ID))

# Create an auction listing by a seller
listing = create_listing("Healing potion", "seller_123", price=40, quantity=2, duration_hours=1)
print("Created auction listing:", listing)

# Buyer buys 1 from auction
ok, res = buy_auction_listing(listing.get("item_id"), PLAYER_ID, quantity=1)
print("Buy from auction ->", ok, res)

pdata = load_player_data()
pinv = load_player_inventories()
print("=== After auction purchase ===")
print("Player gold:", pdata[PLAYER_ID]["gold"])
print("Player inventory:", pinv.get(PLAYER_ID))
