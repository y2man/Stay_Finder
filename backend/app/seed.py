from sqlalchemy import select
from .db import SessionLocal
from .models import User, Destination, Property
from .security import hash_pw

DESTINATION_IMAGES = {
    "Addis Ababa": "https://images.unsplash.com/photo-1647316703389-e114712500e5?w=1200&q=80&fit=crop",
    "Lisbon": "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=1200&q=80&fit=crop",
    "Kyoto": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1200&q=80&fit=crop",
}

PROPERTY_IMAGES = [
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1000&q=80&fit=crop",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=1000&q=80&fit=crop",
]

PLACES = [
    ("Addis Ababa", "Ethiopia", 9.03, 38.74),
    ("Lisbon", "Portugal", 38.72, -9.14),
    ("Kyoto", "Japan", 35.01, 135.77),
]


def run():
    with SessionLocal() as db:
        existing_host = db.scalar(select(User).where(User.email == "host@stayfinder.dev"))
        if db.scalar(select(User).limit(1)):
            # The demo database is persistent, so refresh the old broken Picsum
            # seed URLs during deploy without replacing host-uploaded images.
            if existing_host:
                for destination in db.scalars(select(Destination).where(Destination.city.in_(DESTINATION_IMAGES))):
                    if destination.image_url.startswith("https://picsum.photos/"):
                        destination.image_url = DESTINATION_IMAGES[destination.city]
                for prop in db.scalars(select(Property).where(Property.host_id == existing_host.id)):
                    if prop.image_url.startswith("https://picsum.photos/") and prop.title.startswith(("Modern ", "Sunlit ", "Quiet ")):
                        city = prop.destination.city
                        place_index = next((i for i, place in enumerate(PLACES) if place[0] == city), None)
                        type_index = {"Modern": 0, "Sunlit": 1, "Quiet": 2}.get(prop.title.split(" ", 1)[0])
                        if place_index is not None and type_index is not None:
                            prop.image_url = PROPERTY_IMAGES[place_index * 3 + type_index]
                db.commit()
            return
        host = User(email="host@stayfinder.dev", password_hash=hash_pw("password123"), full_name="Demo Host", role="host")
        db.add(host)
        for i, (city, country, la, lo) in enumerate(PLACES):
            d = Destination(city=city, country=country, image_url=DESTINATION_IMAGES[city]); db.add(d); db.flush()
            for j, (cat, price) in enumerate([("apartment", 60), ("villa", 220), ("house", 120)]):
                db.add(Property(host_id=host.id, destination_id=d.id, title=f"{['Modern','Sunlit','Quiet'][j]} {cat} in {city}",
                    description=f"A comfortable {cat} in {city}.", category=cat, price_per_night=price + i * 10,
                    cleaning_fee=15, bedrooms=j + 1, bathrooms=1 + j // 2, max_guests=2 + j * 2, rating=4.2 + j * 0.3,
                    latitude=la, longitude=lo, image_url=PROPERTY_IMAGES[i * 3 + j],
                    amenities=["wifi", "kitchen"]))
        db.commit()

if __name__ == "__main__": run()
