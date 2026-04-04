from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponce)
async def register(user_data: UserRegister, auth_service : AuthService = Depends(get_auth_service)):
    user = await auth_service.register(
        name = user_data.name, 
        email = user_data.email,
        password = user_data.password
        )
    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    token = await auth_service.login(
        name = user_data.name,
        password = user_data.password
    )
    return token

@router.post("logout", response_model=JSONResponse)
async def logout():
    return JSONResponse(
        status_code=200,
        details = "OK"
    )