FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/customer-env && chmod 0777 /home/user/customer-env

RUN cat <<'EOF' > /home/user/customer-env/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
apprunner:x:1005:1005:App Runner:/home/apprunner:/bin/bash
EOF

RUN cat <<'EOF' > /home/user/customer-env/group
root:x:0:
daemon:x:1:
bin:x:2:
sys:x:3:
adm:x:4:
tty:x:5:
disk:x:6:
lp:x:7:
mail:x:8:
news:x:9:
uucp:x:10:
man:x:12:
proxy:x:13:
kmem:x:15:
dialout:x:20:
fax:x:21:
voice:x:22:
cdrom:x:24:
floppy:x:25:
tape:x:26:
sudo:x:27:
audio:x:29:
dip:x:30:
www-data:x:33:
backup:x:34:
operator:x:37:
list:x:38:
irc:x:39:
src:x:40:
shadow:x:42:
utmp:x:43:
video:x:44:
sasl:x:45:
plugdev:x:46:
staff:x:50:
games:x:60:
users:x:100:
nogroup:x:65534:
apprunner:x:1005:
datawriters:x:1020:appruner
EOF

RUN cat <<'EOF' > /home/user/customer-env/shadow
root:*:19738:0:99999:7:::
daemon:*:19738:0:99999:7:::
bin:*:19738:0:99999:7:::
sys:*:19738:0:99999:7:::
sync:*:19738:0:99999:7:::
games:*:19738:0:99999:7:::
man:*:19738:0:99999:7:::
lp:*:19738:0:99999:7:::
mail:*:19738:0:99999:7:::
news:*:19738:0:99999:7:::
uucp:*:19738:0:99999:7:::
proxy:*:19738:0:99999:7:::
www-data:*:19738:0:99999:7:::
backup:*:19738:0:99999:7:::
list:*:19738:0:99999:7:::
irc:*:19738:0:99999:7:::
nobody:*:19738:0:99999:7:::
apprunner:$6$rounds=5000$saltsalt$hashedpasswordhere:19738:0:99999:7:::
EOF

RUN cat <<'EOF' > /home/user/customer-env/perms.txt
/srv/data/:
total 8
drwxr-xr-x 3 root root        4096 Jan 15 10:00 .
drwxr-xr-x 3 root root        4096 Jan 15 09:55 ..
drwxrwx--- 2 root datawriters 4096 Jan 15 10:00 uploads

File: /srv/data/uploads
Access: (0770/drwxrwx---)  Uid: (0/root)   Gid: (1020/datawriters)
EOF

RUN cat <<'EOF' > /home/user/customer-env/notes.txt
Ticket #4891
Customer says they ran: usermod -aG datawriters apprunner
But user still can't write to /srv/data/uploads
Asked them to verify with 'groups apprunner' - they said it shows datawriters
???
EOF

RUN chmod 0666 /home/user/customer-env/passwd && \
    chmod 0666 /home/user/customer-env/group && \
    chmod 0666 /home/user/customer-env/shadow && \
    chmod 0666 /home/user/customer-env/perms.txt && \
    chmod 0666 /home/user/customer-env/notes.txt

RUN useradd -m -d /home/user -s /bin/bash -u 1000 user || true

RUN chown -R user:user /home/user

WORKDIR /home/user

USER user

CMD ["/bin/bash"]
