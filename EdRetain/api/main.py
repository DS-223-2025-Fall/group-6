from fastapi import FastAPI, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from Database.database import get_db
from Database.models import (
    DimUser, DimDate, DimSubscriptionPlan, DimCampaign, DimChannel,
    FactUserDailyActivity, FactCampaignInteraction, FactUserAnalyticsSnapshot,
)
from Database.schemas import (
    DimUserCreate, DimUserSchema,
    DimDateCreate, DimDateSchema,
    DimSubscriptionPlanCreate, DimSubscriptionPlanSchema,
    DimCampaignCreate, DimCampaignSchema,
    DimChannelCreate, DimChannelSchema,
    FactUserDailyActivityCreate, FactUserDailyActivitySchema,
    FactCampaignInteractionCreate, FactCampaignInteractionSchema,
    FactUserAnalyticsSnapshotCreate, FactUserAnalyticsSnapshotSchema,
)

app = FastAPI(title="Project API")

# -------- DIMUSER CRUD --------
@app.get("/users", response_model=list[DimUserSchema])
def get_users(db: Session = Depends(get_db)):
    users = db.query(DimUser).all()
    return users

@app.post("/users", response_model=DimUserSchema, status_code=status.HTTP_201_CREATED)
def add_user(user: DimUserCreate, db: Session = Depends(get_db)):
    db_user = DimUser(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/users/{user_key}", response_model=DimUserSchema)
def update_user(user_key: int, user_update: DimUserCreate, db: Session = Depends(get_db)):
    user = db.query(DimUser).filter(DimUser.user_key == user_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user_update.dict().items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/users/{user_key}")
def delete_user(user_key: int, db: Session = Depends(get_db)):
    user = db.query(DimUser).filter(DimUser.user_key == user_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# -------- PLANS CRUD --------
@app.get("/plans", response_model=list[DimSubscriptionPlanSchema])
def get_plans(db: Session = Depends(get_db)):
    return db.query(DimSubscriptionPlan).all()

@app.post("/plans", response_model=DimSubscriptionPlanSchema, status_code=status.HTTP_201_CREATED)
def add_plan(plan: DimSubscriptionPlanCreate, db: Session = Depends(get_db)):
    db_plan = DimSubscriptionPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

@app.put("/plans/{subscription_plan_key}", response_model=DimSubscriptionPlanSchema)
def update_plan(subscription_plan_key: int, plan_update: DimSubscriptionPlanCreate, db: Session = Depends(get_db)):
    plan = db.query(DimSubscriptionPlan).filter(DimSubscriptionPlan.subscription_plan_key == subscription_plan_key).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for k, v in plan_update.dict().items():
        setattr(plan, k, v)
    db.commit()
    db.refresh(plan)
    return plan

@app.delete("/plans/{subscription_plan_key}")
def delete_plan(subscription_plan_key: int, db: Session = Depends(get_db)):
    plan = db.query(DimSubscriptionPlan).filter(DimSubscriptionPlan.subscription_plan_key == subscription_plan_key).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return {"success": True, "message": "Plan deleted successfully"}

# -------- DIMDATE CRUD --------
@app.get("/dates", response_model=list[DimDateSchema])
def get_dates(db: Session = Depends(get_db)):
    return db.query(DimDate).all()

@app.post("/dates", response_model=DimDateSchema, status_code=status.HTTP_201_CREATED)
def add_date(date: DimDateCreate, db: Session = Depends(get_db)):
    db_date = DimDate(**date.dict())
    db.add(db_date)
    db.commit()
    db.refresh(db_date)
    return db_date

@app.put("/dates/{date_key}", response_model=DimDateSchema)
def update_date(date_key: int, date_update: DimDateCreate, db: Session = Depends(get_db)):
    date_row = db.query(DimDate).filter(DimDate.date_key == date_key).first()
    if not date_row:
        raise HTTPException(status_code=404, detail="Date not found")
    for k, v in date_update.dict().items():
        setattr(date_row, k, v)
    db.commit()
    db.refresh(date_row)
    return date_row

@app.delete("/dates/{date_key}")
def delete_date(date_key: int, db: Session = Depends(get_db)):
    date_row = db.query(DimDate).filter(DimDate.date_key == date_key).first()
    if not date_row:
        raise HTTPException(status_code=404, detail="Date not found")
    db.delete(date_row)
    db.commit()
    return {"success": True, "message": "Date deleted successfully"}

# -- You can repeat this pattern for remaining tables: Campaign, Channel, FactUserDailyActivity, etc.
# For brevity, full CRUD patterns are omitted, but structure is identical.

# -------- Example Analytic Endpoint --------
@app.get("/count_risk_customers")
def count_risk_customers(db: Session = Depends(get_db), threshold: float = Query(0.7)):
    risk_customers = db.query(FactUserAnalyticsSnapshot).filter(FactUserAnalyticsSnapshot.churn_probability >= threshold).count()
    return {"count_risk_customers": risk_customers}

# -------- Dummy Endpoints for Milestone 2 --------
@app.get("/dummy")
def dummy_get():
    return {"msg": "GET working"}

@app.post("/dummy")
def dummy_post(data: dict):
    return {"msg": "POST working", "data": data}

@app.put("/dummy")
def dummy_put(data: dict):
    return {"msg": "PUT working", "data": data}

@app.delete("/dummy")
def dummy_delete():
    return {"msg": "DELETE working"}
