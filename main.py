import uvicorn
from sqlalchemy.orm import Session
from typing import Annotated, Optional
from jose import jwt, JWTError
import os
from datetime import datetime as _dt, timedelta
from passlib.context import CryptContext
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi import Request
import requests
import httpx


import schemas
import crud
import models
import utils

from database import SessionLocal, engine
import logging

# ENVファイルからの環境変数読み込み
load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]

# パスワードのハッシュ化関数を定義
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DBの作成
models.Base.metadata.create_all(bind=engine)


app = FastAPI()


# CORS関連設定
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:5173/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 環境変数設定
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# DBセッションの作成


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="token", auto_error=False)


def get_google_provider_cfg():
    google_discovery_url = "https://accounts.google.com/.well-known/openid-configuration"
    response = requests.get(google_discovery_url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to obtain Google provider configuration")
    return response.json()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    try:
        payload = jwt.decode(token, SECRET_KEY,
                             algorithms=[ALGORITHM])
        email = payload.get("sub")  # ここで、email を取得
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    # ここで get_user_by_user_email を呼び出す
    user = await crud.get_user_by_user_email(db, email)
    print(user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def get_current_user_optional(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[models.User]:
    print("token:", token)
    if token is None:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("payload:", payload)
        username = payload.get("sub")
    except JWTError as e:
        print(f"JWTError: {e}")
        return None

    user = await crud.get_user_by_username(db, username)
    # print(user)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app.get("/")
def Hello():
    return {"Hello": "World!"}


@app.get("/portfolios")
async def get_all_portfolios(db: Session = Depends(get_db)):
    return await crud.get_all_portfolios(db=db)


@app.get("/portfolios/user", response_model=schemas.AllPortfoliosDetail)
async def read_portfolios_by_user_id(
    current_user: models.User = Depends(get_current_user),  # 追加
    db: Session = Depends(get_db),
):
    return await crud.get_all_portfolios_by_user_id(db, current_user.id)  # 変更


@app.get("/portfolio/{portfolio_id}", response_model=schemas.PortfolioDetail)
async def get_portfolio_by_id(portfolio_id: int, db: Session = Depends(get_db)):
    return await crud.get_portfolio(db=db, portfolio_id=portfolio_id)


@app.post("/portfolio")
async def create_portfolio(
    *,
    db: Session = Depends(get_db),
    portfolio: schemas.PortfolioDetailCreate,
    current_user: Optional[schemas.User] = Depends(get_current_user_optional),
):

    # user_id を渡す
    return await crud.create_portfolio(db=db, portfolio=portfolio, user_id=portfolio.user_id)


@app.put("/portfolio/{id}")
async def put_portfolio(id, portfolio):
    return 1


@app.delete("/portfolio/{id}")
async def delete_portfolio(id):
    return 1


@app.get("/portfolio/{portfolio_id}/price_data", response_model=schemas.PortfolioCompositePriceByDate)
async def get_portfolio_price_data_by_id(portfolio_id: int, db: Session = Depends(get_db)):
    return await utils.getPriceData(db=db, portfolio_id=portfolio_id)


@app.get("/portfolios/{user_id}")
async def get_portfolios_by_user_id(user_id: int, db: Session = Depends(get_db)):
    print("Endpoint function-User ID:", user_id)
    return await crud.get_all_portfolios_by_user_id(db=db, user_id=user_id)


@app.post("/portfolio/{portfolio_id}/primary/{user_id}")
async def set_primary_portfolio(user_id: int, portfolio_id: int, db: Session = Depends(get_db)):
    print("Endpoint function-User ID:", user_id)
    print("Endpoint function-Portfolio ID:", portfolio_id)
    await crud.set_primary_portfolio(
        db=db, user_id=user_id, portfolio_id=portfolio_id)
    return await crud.get_all_portfolios_by_user_id(db=db, user_id=user_id)


@app.get("/ticker_list")
async def get_ticker_master(db: Session = Depends(get_db)):
    return await utils.getTickerMaster(db=db)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = _dt.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/sign_up", response_model=schemas.User)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = await crud.get_user_by_user_email(db, email=user.email)
    print(f"db_user: {db_user}")
    if db_user:
        raise HTTPException(status_code=400, detail="Username already in use")
    db_user = await crud.create_user(db=db, user=user)
    return schemas.User.from_orm(db_user)  # この行を追加


@app.post("/sign_in", response_model=schemas.Token)
async def login(form_data: schemas.LoginForm, db: Session = Depends(get_db)):
    user = await crud.get_user_by_user_email(db, email=form_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    if not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires)

    # user_id を含めたレスポンスデータを返す
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}


@app.get("/user/me", response_model=schemas.User)
async def get_user_info(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/auth/google")
async def google_auth(token: str, db: Session = Depends(get_db)):
    user = await crud.authenticate_google_user(db, token)

    if user is None:
        raise HTTPException(
            status_code=400, detail="Google authentication failed")

    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/google/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    # 認証コードを取得
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(
            status_code=400, detail="Missing authentication code")

    # 認証コードを使ってアクセストークンとIDトークンを取得
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://127.0.0.1:8000/auth/google/callback",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = request.post(
        token_endpoint, data=token_data, headers=headers)

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400, detail="Failed to obtain access token")

    token_response_json = token_response.json()
    id_token = token_response_json["id_token"]

    # IDトークンを使ってユーザーを認証
    user = crud.authenticate_google_user(db, id_token)

    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"user_id": user.id}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
