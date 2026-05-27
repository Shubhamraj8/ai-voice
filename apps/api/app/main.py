from fastapi import FastAPI

app = FastAPI(title="AI Voice API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hello-world"}
