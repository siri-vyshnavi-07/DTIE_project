from app.database import Base, engine, SessionLocal
from app import models
from app.security import hash_password
from app.main import issue_qr

Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    for email,name,role,password in [
        ("admin@smartride.local","SmartRide Admin","admin","Admin@12345"),
        ("conductor@smartride.local","Demo Conductor","conductor","Conductor@12345"),
    ]:
        if not db.query(models.User).filter_by(email=email).first():
            code="ST"+role[:2].upper()+"001"
            u=models.User(passenger_code=code,name=name,email=email,phone="",password_hash=hash_password(password),role=role)
            db.add(u);db.commit()
            print(f"Created {role}: {email} / {password}")
        else:
            print(f"{role} already exists: {email}")
finally:
    db.close()
