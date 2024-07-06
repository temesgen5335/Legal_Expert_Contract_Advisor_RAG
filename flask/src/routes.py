from src import app

@app.route("/")
def index():
    return "Hello world! am grown now"