from flask import Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = '2db61f0f3cfdae09d989fe583b4963878ca08019'


from src import routes