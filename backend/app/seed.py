from sqlalchemy import select
from .db import SessionLocal
from .models import User, Destination, Property
from .security import hash_pw

def run():
    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)): return
        host = User(email="host@stayfinder.dev", password_hash=hash_pw("password123"), full_name="Demo Host", role="host")
        db.add(host)
        places = [("Addis Ababa", "Ethiopia", 9.03, 38.74), ("Lisbon", "Portugal", 38.72, -9.14), ("Kyoto", "Japan", 35.01, 135.77)]
        for i, (city, country, la, lo) in enumerate(places):
            d = Destination(city=city, country=country, image_url=f"https://picsum.photos/seed/{city}/800/600"); db.add(d); db.flush()
            for j, (cat, price) in enumerate([("apartment", 60), ("villa", 220), ("house", 120)]):
                db.add(Property(host_id=host.id, destination_id=d.id, title=f"{['Modern','Sunlit','Quiet'][j]} {cat} in {city}",
                    description=f"A comfortable {cat} in {city}.", category=cat, price_per_night=price + i * 10,
                    cleaning_fee=15, bedrooms=j + 1, bathrooms=1 + j // 2, max_guests=2 + j * 2, rating=4.2 + j * 0.3,
                    latitude=la, longitude=lo, image_url=f"https://picsum.photos/seed/{city}{j}/800/600",
                    amenities=["wifi", "kitchen"]))
        db.commit()

if __name__ == "__main__": run()
