"""Extended StayFinder marketplace routes: host tools, social features and integrations."""
import os, uuid, hashlib, secrets, smtplib, json, io
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import URLError
import jwt
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request as RequestObj
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from .db import get_db
from .models import User, Property, Destination, Booking
from .models_extra import RefreshSession, Favorite, Review, Message, Notification, Payment, EmailToken, PasswordResetToken
from .security import current_user, require_role, make_token, hash_pw, verify_pw
from .config import settings

router = APIRouter(prefix='/api/v1')
UPLOAD_DIR = Path(__file__).resolve().parent / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def digest(value: str) -> str: return hashlib.sha256(value.encode()).hexdigest()
def notify(db: Session, user_id, title: str, body: str):
    db.add(Notification(user_id=user_id, title=title, body=body))
def email_is_configured() -> bool:
    return all((settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.SMTP_FROM))

def send_email(to: str, subject: str, body: str):
    if not email_is_configured():
        return False
    msg = EmailMessage(); msg['Subject'] = subject; msg['From'] = settings.SMTP_FROM; msg['To'] = to; msg.set_content(body)
    smtp_cls = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
    with smtp_cls(settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT) as server:
        if not settings.SMTP_USE_SSL:
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD); server.send_message(msg)
    return True

def auth_pair(db: Session, user: User):
    raw = secrets.token_urlsafe(48)
    db.add(RefreshSession(user_id=user.id, token_hash=digest(raw), expires_at=datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_DAYS)))
    return {'access_token': make_token(user.id), 'refresh_token': raw, 'token_type': 'bearer', 'role': user.role}

class RefreshIn(BaseModel): refresh_token: str
@router.post('/auth/refresh')
def refresh(b: RefreshIn, db: Session=Depends(get_db)):
    row = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == digest(b.refresh_token), RefreshSession.revoked.is_(False)))
    if not row or row.expires_at < datetime.now(timezone.utc): raise HTTPException(401, 'Refresh session expired; log in again')
    user = db.get(User, row.user_id)
    if not user: raise HTTPException(401, 'Account no longer exists')
    row.revoked = True; result = auth_pair(db, user); db.commit(); return result

@router.post('/auth/logout')
def logout(b: RefreshIn, db: Session=Depends(get_db)):
    row = db.scalar(select(RefreshSession).where(RefreshSession.token_hash == digest(b.refresh_token)))
    if row: row.revoked = True; db.commit()
    return {'status':'logged_out'}

@router.post('/auth/verify-email/request')
def request_verification(u: User=Depends(current_user), db: Session=Depends(get_db)):
    if u.email_verified: return {'message':'Email already verified'}
    raw=secrets.token_urlsafe(32); db.add(EmailToken(user_id=u.id, token_hash=digest(raw), expires_at=datetime.now(timezone.utc)+timedelta(hours=24))); db.commit()
    sent=send_email(u.email,'Verify your StayFinder email',f'Open this link to verify your email: {settings.FRONTEND_URL}/verify-email?token={raw}')
    return {'message':'Verification token created','email_sent':sent, **({'development_token':raw} if not sent and settings.ENVIRONMENT.lower() != 'production' else {})}

class VerifyIn(BaseModel): token: str
@router.post('/auth/verify-email')
def verify_email(b: VerifyIn, db: Session=Depends(get_db)):
    row=db.scalar(select(EmailToken).where(EmailToken.token_hash==digest(b.token)))
    if not row or row.expires_at < datetime.now(timezone.utc): raise HTTPException(400,'Verification link is invalid or expired')
    u=db.get(User,row.user_id); u.email_verified=True; db.delete(row); db.commit(); return {'message':'Email verified'}

class ForgotPasswordIn(BaseModel): email: str
@router.post('/auth/password/forgot')
def forgot_password(b:ForgotPasswordIn,db:Session=Depends(get_db)):
    user=db.scalar(select(User).where(func.lower(User.email)==b.email.lower()))
    # Always return the same public response to avoid account enumeration.
    if user:
        raw=secrets.token_urlsafe(32); db.add(PasswordResetToken(user_id=user.id,token_hash=digest(raw),expires_at=datetime.now(timezone.utc)+timedelta(minutes=30))); db.commit()
        sent=send_email(user.email,'Reset your StayFinder password',f'Reset your password within 30 minutes: {settings.FRONTEND_URL}/reset-password?token={raw}')
        return {'message':'If the account exists, reset instructions have been created.','email_sent':sent, **({'development_token':raw} if not sent and settings.ENVIRONMENT.lower() != 'production' else {})}
    return {'message':'If the account exists, reset instructions have been created.'}

class ResetPasswordIn(BaseModel): token:str; password:str=Field(min_length=8)
@router.post('/auth/password/reset')
def reset_password(b:ResetPasswordIn,db:Session=Depends(get_db)):
    row=db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash==digest(b.token)))
    if not row or row.expires_at<datetime.now(timezone.utc): raise HTTPException(400,'Reset link is invalid or expired')
    user=db.get(User,row.user_id); user.password_hash=hash_pw(b.password)
    db.query(RefreshSession).filter(RefreshSession.user_id==user.id).update({'revoked':True})
    db.delete(row); db.commit(); return {'message':'Password changed. Please log in again.'}

class PropertyIn(BaseModel):
    title: str=Field(min_length=5,max_length=200); description: str=Field(min_length=20)
    city: str=Field(min_length=2,max_length=100); country: str=Field(min_length=2,max_length=100)
    category: str='apartment'; price_per_night: Decimal=Field(gt=0); cleaning_fee: Decimal=Field(default=0,ge=0)
    bedrooms: int=Field(default=1,ge=0); bathrooms: int=Field(default=1,ge=1); max_guests: int=Field(default=2,ge=1)
    min_nights: int=Field(default=1,ge=1); image_url: str=''; amenities: list[str]=Field(default_factory=list)
    latitude: float|None=None; longitude: float|None=None; published: bool=True

def property_data(p):
    return {'id':p.id,'title':p.title,'description':p.description,'city':p.destination.city,'country':p.destination.country,'category':p.category,'price_per_night':p.price_per_night,'cleaning_fee':p.cleaning_fee,'bedrooms':p.bedrooms,'bathrooms':p.bathrooms,'max_guests':p.max_guests,'min_nights':p.min_nights,'image_url':p.image_url,'amenities':p.amenities,'latitude':p.latitude,'longitude':p.longitude,'published':p.published,'rating':p.rating}

@router.get('/host/properties')
def host_properties(u: User=Depends(require_role('host','admin')), db: Session=Depends(get_db)):
    q=select(Property).where(Property.host_id==u.id).order_by(Property.created_at.desc())
    return [property_data(p) for p in db.scalars(q).unique().all()]

@router.post('/host/properties',status_code=201)
def create_property(b: PropertyIn,u: User=Depends(require_role('host','admin')),db: Session=Depends(get_db)):
    d=db.scalar(select(Destination).where(func.lower(Destination.city)==b.city.lower(),func.lower(Destination.country)==b.country.lower()))
    if not d: d=Destination(city=b.city.strip(),country=b.country.strip(),image_url=b.image_url); db.add(d); db.flush()
    p=Property(host_id=u.id,destination_id=d.id,title=b.title,description=b.description,category=b.category,price_per_night=b.price_per_night,cleaning_fee=b.cleaning_fee,bedrooms=b.bedrooms,bathrooms=b.bathrooms,max_guests=b.max_guests,min_nights=b.min_nights,image_url=b.image_url,amenities=b.amenities,latitude=b.latitude,longitude=b.longitude,published=b.published)
    db.add(p); db.commit(); db.refresh(p); return property_data(p)

@router.put('/host/properties/{pid}')
def update_property(pid: uuid.UUID,b: PropertyIn,u: User=Depends(require_role('host','admin')),db: Session=Depends(get_db)):
    p=db.get(Property,pid)
    if not p or (p.host_id!=u.id and u.role!='admin'): raise HTTPException(404,'Property not found')
    d=db.scalar(select(Destination).where(func.lower(Destination.city)==b.city.lower(),func.lower(Destination.country)==b.country.lower()))
    if not d: d=Destination(city=b.city.strip(),country=b.country.strip(),image_url=b.image_url); db.add(d); db.flush()
    for k,v in b.model_dump().items():
        if k in ('city','country'): continue
        setattr(p,k,v)
    p.destination_id=d.id; db.commit(); db.refresh(p); return property_data(p)

@router.delete('/host/properties/{pid}')
def delete_property(pid: uuid.UUID,u: User=Depends(require_role('host','admin')),db: Session=Depends(get_db)):
    p=db.get(Property,pid)
    if not p or (p.host_id!=u.id and u.role!='admin'): raise HTTPException(404,'Property not found')
    active=db.scalar(select(func.count()).select_from(Booking).where(Booking.property_id==pid,Booking.status.in_(['pending','confirmed'])))
    if active: p.published=False; db.commit(); return {'message':'Listing unpublished because it has bookings'}
    db.delete(p); db.commit(); return {'message':'Listing deleted'}

@router.get('/host/bookings')
def host_bookings(u: User=Depends(require_role('host','admin')),db: Session=Depends(get_db)):
    q=select(Booking,Property,User).join(Property,Booking.property_id==Property.id).join(User,Booking.guest_id==User.id).where(Property.host_id==u.id).order_by(Booking.created_at.desc())
    return [{'id':b.id,'property_id':p.id,'property_title':p.title,'guest_name':g.full_name,'guest_email':g.email,'guest_id':g.id,'check_in':b.check_in,'check_out':b.check_out,'guests':b.guests,'status':b.status,'total':b.total} for b,p,g in db.execute(q).all()]

@router.post('/host/bookings/{bid}/decision')
def booking_decision(bid: uuid.UUID, approve: bool, u: User=Depends(require_role('host','admin')),db: Session=Depends(get_db)):
    b=db.get(Booking,bid); p=db.get(Property,b.property_id) if b else None
    if not b or not p or (p.host_id!=u.id and u.role!='admin'): raise HTTPException(404,'Booking not found')
    if b.status!='pending': raise HTTPException(409,'Only pending bookings can be decided')
    b.status='confirmed' if approve else 'cancelled'; notify(db,b.guest_id,'Booking update',f'Your booking for {p.title} was {b.status}.'); db.commit();
    guest=db.get(User,b.guest_id)
    if guest and email_is_configured():
        try: send_email(guest.email,'StayFinder booking update',f'Your booking for {p.title} was {b.status}.')
        except Exception: pass
    return {'id':b.id,'status':b.status}

@router.get('/favorites')
def favorites(u: User=Depends(current_user),db: Session=Depends(get_db)):
    q=select(Property).join(Favorite,Favorite.property_id==Property.id).where(Favorite.user_id==u.id)
    return [property_data(p) for p in db.scalars(q).unique().all()]
@router.post('/favorites/{pid}')
def add_favorite(pid:uuid.UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
    if not db.get(Property,pid): raise HTTPException(404,'Property not found')
    row=db.scalar(select(Favorite).where(Favorite.user_id==u.id,Favorite.property_id==pid))
    if not row: db.add(Favorite(user_id=u.id,property_id=pid)); db.commit()
    return {'saved':True}
@router.delete('/favorites/{pid}')
def remove_favorite(pid:uuid.UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
    row=db.scalar(select(Favorite).where(Favorite.user_id==u.id,Favorite.property_id==pid))
    if row: db.delete(row); db.commit()
    return {'saved':False}

class ReviewIn(BaseModel): booking_id:uuid.UUID; rating:int=Field(ge=1,le=5); comment:str=Field(min_length=5,max_length=2000)
@router.get('/properties/{pid}/reviews')
def property_reviews(pid:uuid.UUID,db:Session=Depends(get_db)):
    q=select(Review,User).join(User,Review.guest_id==User.id).where(Review.property_id==pid).order_by(Review.created_at.desc())
    return [{'id':r.id,'rating':r.rating,'comment':r.comment,'guest_name':u.full_name,'created_at':r.created_at} for r,u in db.execute(q).all()]
@router.post('/reviews',status_code=201)
def create_review(b:ReviewIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    booking=db.get(Booking,b.booking_id)
    if not booking or booking.guest_id!=u.id or booking.status!='confirmed' or booking.check_out>datetime.now().date(): raise HTTPException(403,'A completed confirmed stay is required to review')
    if db.scalar(select(Review).where(Review.booking_id==booking.id)): raise HTTPException(409,'This stay already has a review')
    r=Review(property_id=booking.property_id,guest_id=u.id,booking_id=booking.id,rating=b.rating,comment=b.comment); db.add(r); db.flush()
    avg=db.scalar(select(func.avg(Review.rating)).where(Review.property_id==booking.property_id)); p=db.get(Property,booking.property_id); p.rating=round(float(avg or 0),2); db.commit(); return {'id':r.id,'rating':r.rating}

class MessageIn(BaseModel): recipient_id:uuid.UUID; body:str=Field(min_length=1,max_length=4000); booking_id:uuid.UUID|None=None
@router.get('/messages')
def messages(other_user:uuid.UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
    q=select(Message).where(or_((Message.sender_id==u.id)&(Message.recipient_id==other_user),(Message.sender_id==other_user)&(Message.recipient_id==u.id))).order_by(Message.created_at.asc()).limit(300)
    rows=db.scalars(q).all()
    for m in rows:
        if m.recipient_id==u.id: m.read=True
    db.commit()
    return [{'id':m.id,'sender_id':m.sender_id,'recipient_id':m.recipient_id,'body':m.body,'read':m.read,'created_at':m.created_at} for m in rows]
@router.post('/messages',status_code=201)
def send_message(b:MessageIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    recipient=db.get(User,b.recipient_id)
    if not recipient or recipient.id==u.id: raise HTTPException(404,'Recipient not found')
    if not b.booking_id:
        raise HTTPException(422,'A booking is required to start a conversation')
    booking=db.get(Booking,b.booking_id); prop=db.get(Property,booking.property_id) if booking else None
    if not booking or not prop or u.id not in (booking.guest_id,prop.host_id) or recipient.id not in (booking.guest_id,prop.host_id): raise HTTPException(403,'You are not part of this booking')
    m=Message(sender_id=u.id,recipient_id=recipient.id,booking_id=b.booking_id,body=b.body); db.add(m); notify(db,recipient.id,'New message',f'You received a message from {u.full_name}.'); db.commit(); db.refresh(m); return {'id':m.id,'created_at':m.created_at}

@router.get('/notifications')
def notifications(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Notification).where(Notification.user_id==u.id).order_by(Notification.created_at.desc()).limit(100)).all()
    return [{'id':n.id,'title':n.title,'body':n.body,'read':n.read,'created_at':n.created_at} for n in rows]
@router.post('/notifications/{nid}/read')
def read_notification(nid:uuid.UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
    n=db.get(Notification,nid)
    if not n or n.user_id!=u.id: raise HTTPException(404,'Notification not found')
    n.read=True; db.commit(); return {'read':True}

@router.post('/uploads/image')
async def upload_image(file:UploadFile=File(...),u:User=Depends(require_role('host','admin'))):
    allowed={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}
    if file.content_type not in allowed: raise HTTPException(415,'Only JPG, PNG and WebP images are accepted')
    content=await file.read(8*1024*1024+1)
    if len(content)>8*1024*1024: raise HTTPException(413,'Image must be 8 MB or smaller')
    # Prefer durable Cloudinary storage in production; local disk is a development fallback.
    if settings.UPLOAD_PROVIDER.lower() == 'cloudinary' or (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
        if not (settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY and settings.CLOUDINARY_API_SECRET):
            raise HTTPException(503, 'Cloudinary upload is selected but its credentials are incomplete')
        try:
            import cloudinary
            from cloudinary.uploader import upload as cloudinary_upload
            cloudinary.config(cloud_name=settings.CLOUDINARY_CLOUD_NAME, api_key=settings.CLOUDINARY_API_KEY, api_secret=settings.CLOUDINARY_API_SECRET, secure=True)
            result = cloudinary_upload(io.BytesIO(content), folder='stayfinder/properties', resource_type='image')
            return {'url': result['secure_url'], 'storage': 'cloudinary'}
        except ImportError:
            raise HTTPException(503, 'Install the cloudinary dependency to enable Cloudinary uploads')
        except Exception:
            raise HTTPException(502, 'Image storage provider could not accept the upload')
    name=f'{uuid.uuid4().hex}{allowed[file.content_type]}'; (UPLOAD_DIR/name).write_bytes(content)
    return {'url':f'/uploads/{name}', 'storage':'local'}

@router.post('/payments/checkout')
def checkout(booking_id:uuid.UUID,u:User=Depends(current_user),db:Session=Depends(get_db)):
    if not settings.STRIPE_SECRET_KEY: raise HTTPException(503,'Payments are not configured yet. Add STRIPE_SECRET_KEY to backend/.env')
    try: import stripe
    except ImportError: raise HTTPException(503,'Install the Stripe backend dependency first')
    stripe.api_key=settings.STRIPE_SECRET_KEY
    b=db.get(Booking,booking_id)
    if not b or b.guest_id!=u.id: raise HTTPException(404,'Booking not found')
    if b.status != 'confirmed': raise HTTPException(409,'The host must approve this booking before payment')
    session=stripe.checkout.Session.create(mode='payment',success_url=settings.FRONTEND_URL+'/payment/success?session_id={CHECKOUT_SESSION_ID}',cancel_url=settings.FRONTEND_URL+'/trips',line_items=[{'price_data':{'currency':settings.PAYMENT_CURRENCY.lower(),'product_data':{'name':'StayFinder booking'},'unit_amount':int(Decimal(b.total)*100)},'quantity':1}],metadata={'booking_id':str(b.id)})
    payment=db.scalar(select(Payment).where(Payment.booking_id==b.id))
    if payment: payment.provider_reference=session.id; payment.status='pending'; payment.amount=b.total
    else: db.add(Payment(booking_id=b.id,provider_reference=session.id,amount=b.total,currency=settings.PAYMENT_CURRENCY.lower(),status='pending'))
    db.commit()
    return {'checkout_url':session.url}

@router.post('/payments/webhook')
async def payment_webhook(request:RequestObj,db:Session=Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET: raise HTTPException(503,'Stripe webhook is not configured')
    try:
        import stripe
        event=stripe.Webhook.construct_event(await request.body(),request.headers.get('stripe-signature',''),settings.STRIPE_WEBHOOK_SECRET)
    except Exception: raise HTTPException(400,'Invalid payment webhook signature')
    if event['type'] in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        obj=event['data']['object']; payment=db.scalar(select(Payment).where(Payment.provider_reference==obj['id']))
        if payment and obj.get('payment_status') == 'paid' and payment.status != 'paid':
            payment.status='paid'; booking=db.get(Booking,payment.booking_id); booking.status='confirmed'; notify(db,booking.guest_id,'Payment confirmed','Your StayFinder booking is confirmed.'); guest=db.get(User,booking.guest_id);
            if guest and email_is_configured():
                try: send_email(guest.email,'StayFinder payment confirmed','Your payment was received and your booking is confirmed.')
                except Exception: pass
    db.commit(); return {'received':True}

class AssistantIn(BaseModel): message:str=Field(min_length=2,max_length=2000)
@router.post('/assistant')
def assistant(b:AssistantIn,u:User=Depends(current_user)):
    if not settings.GROQ_API_KEY: raise HTTPException(503,'AI assistant is not configured. Add GROQ_API_KEY to backend/.env')
    payload={'model':settings.GROQ_MODEL,'messages':[{'role':'system','content':'You are StayFinder travel support. Help users compare accommodation needs, explain booking steps and suggest useful search filters. Do not claim to have checked live availability or make bookings. Keep answers concise.'},{'role':'user','content':b.message}],'temperature':0.4}
    req=Request('https://api.groq.com/openai/v1/chat/completions',data=json.dumps(payload).encode(),headers={
    'Authorization': f'Bearer {settings.GROQ_API_KEY}',
    'Content-Type': 'application/json',
    'User-Agent': 'StayFinder/1.0'
},method='POST')
    try:
        with urlopen(req,timeout=25) as response: data=json.loads(response.read())
        return {'reply':data['choices'][0]['message']['content']}
    except Exception: raise HTTPException(502,'The AI service could not respond. Please try again.')

@router.get('/admin/overview')
def admin_overview(u:User=Depends(require_role('admin')),db:Session=Depends(get_db)):
    return {'users':db.scalar(select(func.count()).select_from(User)),'properties':db.scalar(select(func.count()).select_from(Property)),'bookings':db.scalar(select(func.count()).select_from(Booking)),'revenue':db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.status=='paid'))}

@router.get('/admin/properties')
def admin_properties(u:User=Depends(require_role('admin')),db:Session=Depends(get_db)):
    return [{'id':p.id,'title':p.title,'host_id':p.host_id,'published':p.published,'city':p.destination.city,'country':p.destination.country} for p in db.scalars(select(Property).order_by(Property.created_at.desc()).limit(500)).unique().all()]
@router.patch('/admin/properties/{pid}/publish')
def admin_publish(pid:uuid.UUID,published:bool,u:User=Depends(require_role('admin')),db:Session=Depends(get_db)):
    p=db.get(Property,pid)
    if not p: raise HTTPException(404,'Property not found')
    p.published=published; db.commit(); return {'id':p.id,'published':p.published}

@router.get('/admin/users')
def admin_users(u:User=Depends(require_role('admin')),db:Session=Depends(get_db)):
    return [{'id':x.id,'name':x.full_name,'email':x.email,'role':x.role,'created_at':x.created_at} for x in db.scalars(select(User).order_by(User.created_at.desc()).limit(500)).all()]
class RoleIn(BaseModel): role:str=Field(pattern='^(guest|host|admin)$')
@router.patch('/admin/users/{uid}/role')
def admin_role(uid:uuid.UUID,b:RoleIn,u:User=Depends(require_role('admin')),db:Session=Depends(get_db)):
    target=db.get(User,uid)
    if not target: raise HTTPException(404,'User not found')
    target.role=b.role; db.commit(); return {'id':target.id,'role':target.role}
