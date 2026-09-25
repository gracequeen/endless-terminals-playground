# Docker IP Pool Expansion

## Problem
Docker's default address pool runs out of subnets when many concurrent Harbor jobs
create networks (default: ~31 `/20` subnets from `172.17.0.0/12`).

## Fix
Added `default-address-pools` to `/etc/docker/daemon.json`:

```json
{
    "runtimes": {
        "nvidia": {
            "args": [],
            "path": "nvidia-container-runtime"
        }
    },
    "default-address-pools": [
        {"base": "172.17.0.0/12", "size": 24}
    ]
}
```

`/24` subnets from the `172.17.0.0/12` base gives ~4096 possible networks.

## Applied
- Backup saved to `~/daemon.json.bak`
- `sudo systemctl restart docker` required (reload is not sufficient)

## Verified
New networks receive `/24` subnets (e.g. `172.16.2.0/24`) confirming the config is active.
