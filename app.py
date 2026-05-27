from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

import asyncio
from agent import mcp_agent

app = Flask(__name__)


# initialize once
initialized = False


@app.before_request
def startup():

    global initialized

    if not initialized:
        asyncio.run(
            mcp_agent.initialize()
        )

        initialized = True


@app.route("/")
def home():
    return render_template(
        "index.html"
    )


@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    user_message = (
        request.json["message"]
    )

    response = asyncio.run(
        mcp_agent.chat(
            user_message
        )
    )

    return jsonify({
        "response": response
    })


if __name__ == "__main__":
    print("Starting Flask...")
    app.run(debug=True)