import requests
import time
import random
import os

# ====== CONFIG ======
servers = {
    "s1": "http://192.168.20.27:8001/info", #đổi thành ip của máy window mình
    "s2": "http://192.168.20.27:8002/info"   #đổi thành ip của máy window mình

}

actions = [
    (7, 3),
    (5, 5),
    (3, 7)
]

Q = {
    "fast": [0, 0, 0],
    "slow": [0, 0, 0]
}

alpha = 0.1
epsilon = 0.2

# ====== FUNCTIONS ======

def measure_response(url):
    try:
        start = time.time()
        requests.get(url, timeout=1)
        return time.time() - start
    except:
        return 2  # lỗi → rất chậm

def get_state():
    t1 = measure_response(servers["s1"])
    t2 = measure_response(servers["s2"])

    avg = (t1 + t2) / 2

    if avg < 0.3:
        return "fast"
    else:
        return "slow"

def choose_action(state):
    if random.random() < epsilon:
        return random.randint(0, 2)
    return Q[state].index(max(Q[state]))

def get_reward():
    t1 = measure_response(servers["s1"])
    t2 = measure_response(servers["s2"])

    avg = (t1 + t2) / 2

    if avg < 0.3:
        return 1
    elif avg < 1:
        return 0
    else:
        return -1

def update_q(state, action, reward):
    Q[state][action] += alpha * (reward - Q[state][action])

def update_haproxy(w1, w2):
    config = f"""
frontend http_front
    bind *:80
    default_backend flask_servers

backend flask_servers
    balance roundrobin
    option httpchk GET /health

    server s1 192.168.20.27:8001 weight {w1} check  #đổi thành ip của máy window mình
    server s2 192.168.20.27:8002 weight {w2} check   #đổi thành ip của máy window mình

"""

    with open("/tmp/haproxy.cfg", "w") as f:
        f.write(config)

    os.system("sudo cp /tmp/haproxy.cfg /etc/haproxy/haproxy.cfg")
    os.system("sudo systemctl reload haproxy")

# ====== MAIN LOOP ======

while True:
    state = get_state()

    action = choose_action(state)
    w1, w2 = actions[action]

    print(f"State: {state} | Action: {w1}-{w2}")

    update_haproxy(w1, w2)

    reward = get_reward()

    update_q(state, action, reward)

    print(f"Reward: {reward}")
    print(f"Q-table: {Q}")

    time.sleep(5)
