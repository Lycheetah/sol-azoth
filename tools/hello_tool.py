#!/usr/bin/env python3
"""
VAEL-SP Hello Tool — test tool for the dynamic tool loader.
Registers a simple /hello command that greets the user.
"""


def register():
    return {
        "name": "hello",
        "description": "Greet the user with a customizable message",
        "safety_level": "safe",
        "params": [
            {
                "name": "name",
                "type": "string",
                "description": "Who to greet",
                "required": False,
                "default": "Mac"
            },
            {
                "name": "style",
                "type": "string",
                "description": "Greeting style: casual, formal, or vael",
                "required": False,
                "default": "vael"
            }
        ],
        "handler": hello_handler
    }


def hello_handler(name="Mac", style="vael"):
    """Handle the hello command."""
    styles = {
        "casual": f"Hey {name}! What's up?",
        "formal": f"Greetings, {name}. How may I assist you today?",
        "vael": f"◆ {name} — the Athanor burns. What shall we forge?"
    }
    msg = styles.get(style, styles["vael"])
    return {"message": msg, "style": style, "addressee": name}
