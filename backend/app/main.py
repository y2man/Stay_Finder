import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, Property, Destination, Booking
from .security import hash_pw, verify_pw, make_token, current_user
from .models_extra import RefreshSession, Favorite, Review, Message, Notification, Payment, EmailToken
from .extra_routes import router as extra_router, auth_pair, notify, send_email, email_is_configured
from fastapi.staticfiles import StaticFiles
from pathlib import Path

if settings.ENVIRONMENT.lower() == "production" and (len(settings.SECRET_KEY) < 32 or "replace-this" in settings.SECRET_KEY):
    raise RuntimeError("Production requires a strong SECRET_KEY of at least 32 characters")

app = FastAPI(title="StayFinder API", version="1.1")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.CORS_ORIGINS.split(",")],
                   allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
app.include_router(extra_router)
app.mount("/uploads", StaticFiles(directory=str(Path(__file__).resolve().parent / "uploads")), name="uploads")
q2 = lambda d: Decimal(d).quantize(Decimal("0.01"), ROUND_HALF_UP)

@app.get("/api/v1/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("select 1")); return {"status": "ok"}

# ---- auth
class RegisterIn(BaseModel):
    email: EmailStr; password: str = Field(min_length=8); full_name: str = Field(min_length=1, max_length=120)
    role: str = Field("guest", pattern="^(guest|host)$")
class LoginIn(BaseModel):
    email: EmailStr; password: str

@app.post("/api/v1/auth/register", status_code=201)
def register(b: RegisterIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == b.email.lower())):
        raise HTTPException(409, "Email already registered")
    u = User(email=b.email.lower(), password_hash=hash_pw(b.password), full_name=b.full_name, role=b.role)
    if u.email in [x.strip().lower() for x in settings.ADMIN_EMAILS.split(",") if x.strip()]: u.role = "admin"
    db.add(u); db.flush(); result = auth_pair(db, u); db.commit()
    return result

@app.post("/api/v1/auth/login")
def login(b: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == b.email.lower()))
    if not u or not verify_pw(u.password_hash, b.password): raise HTTPException(401, "Wrong email or password")
    result = auth_pair(db, u); db.commit(); return result

@app.get("/api/v1/users/me")
def me(u: User = Depends(current_user)):
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role}

# ---- properties
def prop_out(p: Property):
    return {"id": p.id, "title": p.title, "city": p.destination.city, "country": p.destination.country,
            "price_per_night": p.price_per_night, "rating": p.rating, "bedrooms": p.bedrooms,
            "max_guests": p.max_guests, "image_url": p.image_url, "category": p.category}

@app.get("/api/v1/destinations")
def destinations(db: Session = Depends(get_db)):
    rows = db.execute(select(Destination, func.count(Property.id)).outerjoin(Property).group_by(Destination.id)).all()
    return [{"id": d.id, "city": d.city, "country": d.country, "image_url": d.image_url, "properties": n} for d, n in rows]

@app.get("/api/v1/properties")
def list_properties(q: str | None = None, min_price: float | None = None, max_price: float | None = None,
                    category: str | None = None, bedrooms: int | None = None, guests: int | None = None,
                    check_in: date | None = None, check_out: date | None = None,
                    sort: str = Query("popular", pattern="^(popular|price_asc|price_desc|rating)$"),
                    page: int = Query(1, ge=1), size: int = Query(12, ge=1, le=50), db: Session = Depends(get_db)):
    s = select(Property).join(Destination).where(Property.published.is_(True))
    if q:
        like = f"%{q}%"
        s = s.where(Property.title.ilike(like) | Destination.city.ilike(like) | Destination.country.ilike(like))
    if min_price is not None: s = s.where(Property.price_per_night >= min_price)
    if max_price is not None: s = s.where(Property.price_per_night <= max_price)
    if category: s = s.where(Property.category == category)
    if bedrooms: s = s.where(Property.bedrooms >= bedrooms)
    if guests: s = s.where(Property.max_guests >= guests)
    if check_in and check_out:
        if check_out <= check_in: raise HTTPException(422, "Check-out must be after check-in")
        busy = select(Booking.property_id).where(Booking.status.in_(["pending", "confirmed"]),
                                                  Booking.check_in < check_out, Booking.check_out > check_in)
        s = s.where(Property.id.not_in(busy))
    total = db.scalar(select(func.count()).select_from(s.subquery()))
    order = {"popular": Property.created_at.desc(), "price_asc": Property.price_per_night.asc(),
             "price_desc": Property.price_per_night.desc(), "rating": Property.rating.desc()}[sort]
    rows = db.scalars(s.order_by(order).offset((page - 1) * size).limit(size)).unique().all()
    return {"total": total, "page": page, "items": [prop_out(p) for p in rows]}

@app.get("/api/v1/properties/{pid}")
def get_property(pid: uuid.UUID, db: Session = Depends(get_db)):
    p = db.get(Property, pid)
    if not p or not p.published: raise HTTPException(404, "Property not found")
    return {**prop_out(p), "description": p.description, "bathrooms": p.bathrooms, "amenities": p.amenities,
            "min_nights": p.min_nights, "cleaning_fee": p.cleaning_fee}

# ---- bookings (server-side pricing, DB-enforced no-overlap)
class BookingIn(BaseModel):
    property_id: uuid.UUID; check_in: date; check_out: date; guests: int = Field(ge=1)

def quote(p: Property, ci: date, co: date):
    n = (co - ci).days
    sub = q2(p.price_per_night * n); fee = q2(sub * Decimal(str(settings.SERVICE_FEE_RATE)))
    tax = q2(sub * Decimal(str(settings.TAX_RATE)))
    return n, sub, q2(p.cleaning_fee), fee, tax, q2(sub + p.cleaning_fee + fee + tax)

@app.post("/api/v1/bookings/quote")
def get_quote(b: BookingIn, db: Session = Depends(get_db)):
    p = db.get(Property, b.property_id)
    if not p or not p.published: raise HTTPException(404, "Property not found")
    if b.check_out <= b.check_in: raise HTTPException(422, "Check-out must be after check-in")
    if b.guests > p.max_guests: raise HTTPException(422, f"Maximum {p.max_guests} guests")
    n, sub, cl, fee, tax, tot = quote(p, b.check_in, b.check_out)
    return {"nights": n, "subtotal": sub, "cleaning_fee": cl, "service_fee": fee, "taxes": tax, "total": tot}

@app.post("/api/v1/bookings", status_code=201)
def create_booking(b: BookingIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(Property, b.property_id)
    if not p or not p.published: raise HTTPException(404, "Property not found")
    if p.host_id == u.id: raise HTTPException(403, "You cannot book your own listing")
    if email_is_configured() and not u.email_verified: raise HTTPException(403, "Please verify your email before booking")
    if b.check_in < date.today(): raise HTTPException(422, "Check-in is in the past")
    if b.check_out <= b.check_in: raise HTTPException(422, "Check-out must be after check-in")
    if (b.check_out - b.check_in).days < p.min_nights: raise HTTPException(422, f"Minimum stay is {p.min_nights} nights")
    if b.guests > p.max_guests: raise HTTPException(422, f"Maximum {p.max_guests} guests")
    n, sub, cl, fee, tax, tot = quote(p, b.check_in, b.check_out)
    bk = Booking(property_id=p.id, guest_id=u.id, check_in=b.check_in, check_out=b.check_out, guests=b.guests,
                 subtotal=sub, cleaning_fee=cl, service_fee=fee, taxes=tax, total=tot, status="pending")
    db.add(bk)
    from .extra_routes import notify
    notify(db, p.host_id, "New booking request", f"You received a booking request for {p.title}.")
    try: db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "Those dates are no longer available")
    host = db.get(User, p.host_id)
    if host and email_is_configured():
        try: send_email(host.email, "New StayFinder booking request", f"A guest requested {p.title}. Sign in to review the request.")
        except Exception: pass
    return {"id": bk.id, "status": bk.status, "total": bk.total}

@app.get("/api/v1/bookings/me")
def my_bookings(u: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.execute(select(Booking, Property, Payment).join(Property, Booking.property_id == Property.id).outerjoin(Payment, Payment.booking_id == Booking.id).where(Booking.guest_id == u.id).order_by(Booking.created_at.desc())).all()
    return [{"id": r.id, "property_id": r.property_id, "property_title": p.title, "host_id": p.host_id, "check_in": r.check_in, "check_out": r.check_out,
             "status": r.status, "payment_status": pay.status if pay else "unpaid", "total": r.total} for r, p, pay in rows]

@app.post("/api/v1/bookings/{bid}/cancel")
def cancel(bid: uuid.UUID, u: User = Depends(current_user), db: Session = Depends(get_db)):
    bk = db.get(Booking, bid)
    if not bk or bk.guest_id != u.id: raise HTTPException(404, "Booking not found")
    if bk.status in ("cancelled", "expired"): raise HTTPException(409, "Already closed")
    paid = db.scalar(select(Payment).where(Payment.booking_id == bk.id, Payment.status == "paid"))
    if paid: raise HTTPException(409, "This booking has been paid. Contact the host/support to arrange a refund before cancelling.")
    bk.status = "cancelled"; notify(db, bk.guest_id, "Booking cancelled", "Your booking has been cancelled."); db.commit()
    return {"id": bk.id, "status": bk.status}
