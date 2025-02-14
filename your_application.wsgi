from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, Render!"

if __name__ == "__main__":
    # app.run(debug=True) # 주석 처리
    pass
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, Render!"
