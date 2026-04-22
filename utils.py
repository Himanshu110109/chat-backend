import random

colors = ["red", "blue", "green", "yellow"]
animals = ["tiger", "lion", "panda", "eagle"]

def generate_password():
    return f"{random.choice(colors)}-{random.choice(animals)}-{random.randint(100,999)}"

def sanitize_message(msg):
    return msg[:1000].replace("<", "").replace(">", "")