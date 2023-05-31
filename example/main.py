from fastapi import FastAPI
from webservice import soap

app = FastAPI()

app.include_router(soap)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app")
