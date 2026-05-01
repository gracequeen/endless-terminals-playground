Provisioning script at /home/user/infra/provision.sh was working last week, now it dies halfway through with "VAULT_ADDR: unbound variable". Thing is, VAULT_ADDR is definitely in /home/user/infra/.env — I can see it right there. The script sources that file on line 3. Running `source /home/user/infra/.env && echo $VAULT_ADDR` in my shell prints the value fine, so the file parses okay.

The weird part: some vars from that .env work and some don't. DB_HOST works, REDIS_URL works, but VAULT_ADDR and a couple others fail as unbound. No pattern I can see — they're all just KEY=value lines. Script runs with set -u so any missing var is fatal.

Need provision.sh to complete successfully. It's supposed to write /home/user/infra/output/config.json at the end with all the resolved values.
