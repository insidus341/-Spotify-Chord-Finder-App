from flask import Flask
from app.main import app

app.run(
    host='0.0.0.0', 
    port=8000
)