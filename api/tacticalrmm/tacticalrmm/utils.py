import json
import os
import subprocess
import tldextract

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from agents.models import Agent

notify_error = lambda msg: Response(msg, status=status.HTTP_400_BAD_REQUEST)


def reload_nats():
    users = [{"user": "tacticalrmm", "password": settings.SECRET_KEY}]
    agents = Agent.objects.prefetch_related("user").only("pk", "agent_id")
    for agent in agents:
        users.append({"user": agent.agent_id, "password": agent.user.auth_token.key})

    tld = tldextract.extract(settings.ALLOWED_HOSTS[0])
    domain = tld.domain + "." + tld.suffix
    config = {
        "tls": {
            "cert_file": f"/etc/letsencrypt/live/{domain}/fullchain.pem",
            "key_file": f"/etc/letsencrypt/live/{domain}/privkey.pem",
        },
        "authorization": {"users": users},
        "max_payload": 2048576005,
    }

    conf = os.path.join(settings.BASE_DIR, "nats-rmm.conf")
    with open(conf, "w") as f:
        json.dump(config, f)

    subprocess.run(["/usr/local/bin/nats-server", "-signal", "reload"])
