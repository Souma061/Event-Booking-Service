from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def greet():
    return {"message": "Welcome to the Event Booking Service!"}
