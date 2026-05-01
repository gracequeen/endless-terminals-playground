Been chasing this for hours. We have a deployment config system in /home/user/deploy — services pick up their config from rendered templates. Right now `./render.py staging web-api` is supposed to spit out the final config for the web-api service in staging, but it's returning the wrong database host. Should be `db-staging.internal` but it's giving me `db-prod.internal` which is… not great.

The weird part is I've triple-checked the staging overlay and it definitely has the right db host. And if I render `./render.py production web-api` it correctly gives the prod db. So the override system works, just not for staging somehow? Other services in staging render fine too, it's specifically web-api that's broken.

Config inheritance is base → environment → service → environment+service, pretty standard layering. Something's getting clobbered somewhere in the merge but I can't see where.
