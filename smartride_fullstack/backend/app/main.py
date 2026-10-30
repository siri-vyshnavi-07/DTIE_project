import base64, io, secrets
from datetime import datetime
import qrcode
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
from . import models, schemas
from .security import hash_password, verify_password, create_access_token, new_qr_token, token_digest
from .deps import current_user, require_roles
from .config import FRONTEND_ORIGIN, STOPS, FARE_PER_STOP, MINIMUM_FARE

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SmartRide Bus Pass API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def user_out(u):
    return {"id":u.id,"passenger_code":u.passenger_code,"name":u.name,"email":u.email,"phone":u.phone,"role":u.role,"is_active":u.is_active}

def issue_qr(db, user):
    raw = new_qr_token()
    if user.qr_token:
        user.qr_token.token_hash = token_digest(raw)
        user.qr_token.active = True
        user.qr_token.created_at = datetime.utcnow()
    else:
        user.qr_token = models.QRToken(token_hash=token_digest(raw), active=True)
    db.flush()
    return raw

@app.get("/")
def root():
    return {"message":"SmartRide API is running","docs":"/docs"}

@app.post("/api/auth/register")
def register(data: schemas.RegisterIn, db: Session=Depends(get_db)):
    email = data.email.lower()
    if db.query(models.User).filter(func.lower(models.User.email)==email).first():
        raise HTTPException(409, "An account with this email already exists")
    code = "BP" + secrets.token_hex(4).upper()
    while db.query(models.User).filter_by(passenger_code=code).first():
        code = "BP" + secrets.token_hex(4).upper()
    user = models.User(passenger_code=code,name=data.name,email=email,phone=data.phone,password_hash=hash_password(data.password),role="passenger")
    db.add(user); db.flush()
    user.card = models.SmartCard(card_number="SC"+secrets.token_hex(5).upper(),balance=0)
    raw = issue_qr(db,user)
    db.commit(); db.refresh(user)
    token = create_access_token(user.id,user.role)
    return {"access_token":token,"token_type":"bearer","user":user_out(user),"qr_token":raw}

@app.post("/api/auth/login")
def login(data: schemas.LoginIn, db: Session=Depends(get_db)):
    user=db.query(models.User).filter(func.lower(models.User.email)==data.email.lower()).first()
    if not user or not verify_password(data.password,user.password_hash):
        raise HTTPException(401,"Incorrect email or password")
    response = {"access_token":create_access_token(user.id,user.role),"token_type":"bearer","user":user_out(user)}
    # Issue a fresh QR token at passenger login so the authenticated owner can
    # restore their QR after a new browser session. The previous QR is invalidated.
    if user.role == "passenger":
        response["qr_token"] = issue_qr(db, user)
        db.commit()
    return response

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return user_out(user)

@app.get("/api/passenger/dashboard")
def passenger_dashboard(user=Depends(require_roles("passenger")), db:Session=Depends(get_db)):
    return {"user":user_out(user),"card":{"card_number":user.card.card_number,"balance":user.card.balance},"qr_active":bool(user.qr_token and user.qr_token.active),"stops":STOPS}

@app.get("/api/passenger/qr")
def passenger_qr(user=Depends(require_roles("passenger"))):
    if not user.qr_token or not user.qr_token.active:
        raise HTTPException(404,"No active QR token")
    # Raw token is returned only at issue time; QR image is generated from the one-time token kept client-side.
    raise HTTPException(409,"For security, use the QR token returned at registration or regenerate your QR code.")

@app.post("/api/passenger/qr/regenerate")
def regenerate_qr(data:schemas.RegenerateQRIn,user=Depends(require_roles("passenger")),db:Session=Depends(get_db)):
    raw=issue_qr(db,user);db.commit()
    return {"qr_token":raw,"message":"QR code regenerated. Your previous QR code is now invalid."}

@app.post("/api/passenger/recharge")
def recharge(data:schemas.RechargeIn,user=Depends(require_roles("passenger")),db:Session=Depends(get_db)):
    user.card.balance += data.amount
    db.add(models.Transaction(user_id=user.id,transaction_type="RECHARGE",amount=data.amount,description="Demo wallet recharge"))
    db.commit()
    return {"balance":user.card.balance,"message":"Demo recharge successful. No real payment was collected."}

@app.get("/api/passenger/transactions")
def passenger_transactions(user=Depends(require_roles("passenger")),db:Session=Depends(get_db)):
    rows=db.query(models.Transaction).filter_by(user_id=user.id).order_by(models.Transaction.created_at.desc()).limit(100).all()
    return [{"id":r.id,"type":r.transaction_type,"amount":r.amount,"description":r.description,"created_at":r.created_at.isoformat()} for r in rows]

@app.get("/api/passenger/journeys")
def passenger_journeys(user=Depends(require_roles("passenger")),db:Session=Depends(get_db)):
    rows=db.query(models.Journey).filter_by(passenger_id=user.id).order_by(models.Journey.created_at.desc()).limit(100).all()
    return [{"id":r.id,"from_stop":r.from_stop,"to_stop":r.to_stop,"distance_stops":r.distance_stops,"fare":r.fare,"created_at":r.created_at.isoformat()} for r in rows]

@app.get("/api/stops")
def stops():
    return {"stops":STOPS,"fare_per_stop":FARE_PER_STOP,"minimum_fare":MINIMUM_FARE}

@app.post("/api/conductor/verify")
def verify_qr(payload:dict,user=Depends(require_roles("conductor","admin")),db:Session=Depends(get_db)):
    raw=payload.get("qr_token","")
    if not raw:
        raise HTTPException(400,"QR token is required")
    token=db.query(models.QRToken).filter_by(token_hash=token_digest(raw),active=True).first()
    if not token or not token.user or not token.user.is_active or token.user.role!="passenger":
        raise HTTPException(404,"Invalid, expired or inactive passenger QR code")
    p=token.user
    return {"verified":True,"passenger":user_out(p),"card":{"card_number":p.card.card_number,"balance":p.card.balance}}

@app.post("/api/conductor/journey")
def create_journey(data:schemas.JourneyIn,user=Depends(require_roles("conductor","admin")),db:Session=Depends(get_db)):
    token=db.query(models.QRToken).filter_by(token_hash=token_digest(data.qr_token),active=True).first()
    if not token or not token.user or token.user.role!="passenger" or not token.user.is_active:
        raise HTTPException(404,"Passenger QR code is invalid")
    a=next((s for s in STOPS if s["id"]==data.from_stop_id),None)
    b=next((s for s in STOPS if s["id"]==data.to_stop_id),None)
    if not a or not b: raise HTTPException(400,"Invalid route stop")
    distance=abs(a["sequence"]-b["sequence"])
    if distance==0: raise HTTPException(400,"Boarding and exit stops must be different")
    fare=max(MINIMUM_FARE,distance*FARE_PER_STOP)
    passenger=token.user
    if passenger.card.balance < fare: raise HTTPException(400,"Insufficient smart card balance")
    # Update balance and write both journey and transaction in one database transaction.
    passenger.card.balance-=fare
    journey=models.Journey(passenger_id=passenger.id,conductor_id=user.id,from_stop=a["name"],to_stop=b["name"],distance_stops=distance,fare=fare)
    tx=models.Transaction(user_id=passenger.id,transaction_type="FARE",amount=fare,description=f"{a['name']} to {b['name']}")
    db.add_all([journey,tx]);db.commit()
    return {"message":"Journey recorded and fare deducted","passenger":user_out(passenger),"fare":fare,"balance":passenger.card.balance,"journey_id":journey.id}

@app.get("/api/admin/overview")
def admin_overview(user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    return {"passengers":db.query(models.User).filter_by(role="passenger").count(),"conductors":db.query(models.User).filter_by(role="conductor").count(),"active_passes":db.query(models.User).filter_by(role="passenger",is_active=True).count(),"transactions":db.query(models.Transaction).count(),"revenue":db.query(func.coalesce(func.sum(models.Transaction.amount),0)).filter(models.Transaction.transaction_type=="FARE").scalar()}

@app.get("/api/admin/transactions")
def admin_transactions(user=Depends(require_roles("admin")),db:Session=Depends(get_db)):
    rows=db.query(models.Transaction,models.User).join(models.User,models.Transaction.user_id==models.User.id).order_by(models.Transaction.created_at.desc()).limit(200).all()
    return [{"passenger":u.name,"passenger_code":u.passenger_code,"type":t.transaction_type,"amount":t.amount,"description":t.description,"created_at":t.created_at.isoformat()} for t,u in rows]
