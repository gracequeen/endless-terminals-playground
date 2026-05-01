FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    grep \
    gawk \
    sed \
    coreutils \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN cat <<'EOF' > /var/log/auth_attempts.log
Mar 15 14:22:01 server sshd[12345]: Failed password for invalid user admin from 203.0.113.42 port 54321 ssh2
Mar 15 14:22:05 server sshd[12346]: Failed password for invalid user root from 203.0.113.42 port 54322 ssh2
Mar 15 14:22:10 server sshd[12347]: Failed password for invalid user test from 203.0.113.42 port 54323 ssh2
Mar 15 14:22:15 server sshd[12348]: Failed password for invalid user admin from 203.0.113.42 port 54324 ssh2
Mar 15 14:22:20 server sshd[12349]: Failed password for invalid user user from 203.0.113.42 port 54325 ssh2
Mar 15 14:22:25 server sshd[12350]: Failed password for invalid user guest from 203.0.113.42 port 54326 ssh2
Mar 15 14:22:30 server sshd[12351]: Failed password for invalid user oracle from 203.0.113.42 port 54327 ssh2
Mar 15 14:22:35 server sshd[12352]: Failed password for invalid user mysql from 203.0.113.42 port 54328 ssh2
Mar 15 14:22:40 server sshd[12353]: Failed password for invalid user postgres from 203.0.113.42 port 54329 ssh2
Mar 15 14:22:45 server sshd[12354]: Failed password for invalid user ftp from 203.0.113.42 port 54330 ssh2
Mar 15 14:22:50 server sshd[12355]: Failed password for invalid user www from 203.0.113.42 port 54331 ssh2
Mar 15 14:22:55 server sshd[12356]: Failed password for invalid user apache from 203.0.113.42 port 54332 ssh2
Mar 15 14:23:00 server sshd[12357]: Failed password for invalid user nginx from 203.0.113.42 port 54333 ssh2
Mar 15 14:23:05 server sshd[12358]: Failed password for invalid user tomcat from 203.0.113.42 port 54334 ssh2
Mar 15 14:23:10 server sshd[12359]: Failed password for invalid user jenkins from 203.0.113.42 port 54335 ssh2
Mar 15 14:23:15 server sshd[12360]: Failed password for invalid user git from 203.0.113.42 port 54336 ssh2
Mar 15 14:23:20 server sshd[12361]: Failed password for invalid user svn from 203.0.113.42 port 54337 ssh2
Mar 15 14:23:25 server sshd[12362]: Failed password for invalid user backup from 203.0.113.42 port 54338 ssh2
Mar 15 14:23:30 server sshd[12363]: Failed password for invalid user deploy from 203.0.113.42 port 54339 ssh2
Mar 15 14:23:35 server sshd[12364]: Failed password for invalid user ansible from 203.0.113.42 port 54340 ssh2
Mar 15 14:23:40 server sshd[12365]: Failed password for invalid user puppet from 203.0.113.42 port 54341 ssh2
Mar 15 14:23:45 server sshd[12366]: Failed password for invalid user chef from 203.0.113.42 port 54342 ssh2
Mar 15 14:23:50 server sshd[12367]: Failed password for invalid user salt from 203.0.113.42 port 54343 ssh2
Mar 15 14:24:01 server sshd[12368]: Failed password for invalid user admin from 198.51.100.17 port 55321 ssh2
Mar 15 14:24:05 server sshd[12369]: Failed password for invalid user root from 198.51.100.17 port 55322 ssh2
Mar 15 14:24:10 server sshd[12370]: Failed password for invalid user test from 198.51.100.17 port 55323 ssh2
Mar 15 14:24:15 server sshd[12371]: Failed password for invalid user admin from 198.51.100.17 port 55324 ssh2
Mar 15 14:24:20 server sshd[12372]: Failed password for invalid user user from 198.51.100.17 port 55325 ssh2
Mar 15 14:24:25 server sshd[12373]: Failed password for invalid user guest from 198.51.100.17 port 55326 ssh2
Mar 15 14:24:30 server sshd[12374]: Failed password for invalid user oracle from 198.51.100.17 port 55327 ssh2
Mar 15 14:24:35 server sshd[12375]: Failed password for invalid user mysql from 198.51.100.17 port 55328 ssh2
Mar 15 14:24:40 server sshd[12376]: Failed password for invalid user postgres from 198.51.100.17 port 55329 ssh2
Mar 15 14:24:45 server sshd[12377]: Failed password for invalid user ftp from 198.51.100.17 port 55330 ssh2
Mar 15 14:24:50 server sshd[12378]: Failed password for invalid user www from 198.51.100.17 port 55331 ssh2
Mar 15 14:24:55 server sshd[12379]: Failed password for invalid user apache from 198.51.100.17 port 55332 ssh2
Mar 15 14:25:00 server sshd[12380]: Failed password for invalid user nginx from 198.51.100.17 port 55333 ssh2
Mar 15 14:25:05 server sshd[12381]: Failed password for invalid user tomcat from 198.51.100.17 port 55334 ssh2
Mar 15 14:25:10 server sshd[12382]: Failed password for invalid user jenkins from 198.51.100.17 port 55335 ssh2
Mar 15 14:26:01 server sshd[12383]: Failed password for invalid user admin from 192.0.2.88 port 56321 ssh2
Mar 15 14:26:05 server sshd[12384]: Failed password for invalid user root from 192.0.2.88 port 56322 ssh2
Mar 15 14:26:10 server sshd[12385]: Failed password for invalid user test from 192.0.2.88 port 56323 ssh2
Mar 15 14:26:15 server sshd[12386]: Failed password for invalid user admin from 192.0.2.88 port 56324 ssh2
Mar 15 14:26:20 server sshd[12387]: Failed password for invalid user user from 192.0.2.88 port 56325 ssh2
Mar 15 14:26:25 server sshd[12388]: Failed password for invalid user guest from 192.0.2.88 port 56326 ssh2
Mar 15 14:26:30 server sshd[12389]: Failed password for invalid user oracle from 192.0.2.88 port 56327 ssh2
Mar 15 14:26:35 server sshd[12390]: Failed password for invalid user mysql from 192.0.2.88 port 56328 ssh2
Mar 15 14:26:40 server sshd[12391]: Failed password for invalid user postgres from 192.0.2.88 port 56329 ssh2
Mar 15 14:27:01 server sshd[12392]: Failed password for invalid user admin from 10.0.0.55 port 57321 ssh2
Mar 15 14:27:05 server sshd[12393]: Failed password for invalid user root from 10.0.0.55 port 57322 ssh2
Mar 15 14:27:10 server sshd[12394]: Failed password for invalid user test from 10.0.0.55 port 57323 ssh2
Mar 15 14:27:15 server sshd[12395]: Failed password for invalid user admin from 10.0.0.55 port 57324 ssh2
Mar 15 14:27:20 server sshd[12396]: Failed password for invalid user user from 10.0.0.55 port 57325 ssh2
Mar 15 14:27:25 server sshd[12397]: Failed password for invalid user guest from 10.0.0.55 port 57326 ssh2
Mar 15 14:27:30 server sshd[12398]: Failed password for invalid user oracle from 10.0.0.55 port 57327 ssh2
Mar 15 14:28:01 server sshd[12399]: Failed password for invalid user admin from 172.16.0.12 port 58321 ssh2
Mar 15 14:28:05 server sshd[12400]: Failed password for invalid user root from 172.16.0.12 port 58322 ssh2
Mar 15 14:28:10 server sshd[12401]: Failed password for invalid user test from 172.16.0.12 port 58323 ssh2
Mar 15 14:28:15 server sshd[12402]: Failed password for invalid user admin from 172.16.0.12 port 58324 ssh2
Mar 15 14:28:20 server sshd[12403]: Failed password for invalid user user from 172.16.0.12 port 58325 ssh2
Mar 15 14:29:01 server sshd[12404]: Failed password for invalid user admin from 192.168.1.105 port 59321 ssh2
Mar 15 14:29:05 server sshd[12405]: Failed password for invalid user root from 192.168.1.105 port 59322 ssh2
Mar 15 14:29:10 server sshd[12406]: Failed password for invalid user test from 192.168.1.105 port 59323 ssh2
Mar 15 14:29:15 server sshd[12407]: Failed password for invalid user admin from 192.168.1.105 port 59324 ssh2
Mar 15 14:30:01 server sshd[12408]: Failed password for invalid user admin from 10.1.1.1 port 60321 ssh2
Mar 15 14:30:05 server sshd[12409]: Failed password for invalid user root from 10.1.1.1 port 60322 ssh2
Mar 15 14:30:10 server sshd[12410]: Failed password for invalid user test from 10.1.1.1 port 60323 ssh2
Mar 15 14:31:01 server sshd[12411]: Failed password for invalid user admin from 192.168.0.1 port 61321 ssh2
Mar 15 14:31:05 server sshd[12412]: Failed password for invalid user root from 192.168.0.1 port 61322 ssh2
Mar 15 14:32:01 server sshd[12413]: Failed password for invalid user admin from 172.31.0.5 port 62321 ssh2
Mar 15 14:32:05 server sshd[12414]: Failed password for invalid user root from 172.31.0.5 port 62322 ssh2
Mar 15 14:33:01 server sshd[12415]: Failed password for invalid user admin from 8.8.8.8 port 63321 ssh2
Mar 15 14:34:01 server sshd[12416]: Failed password for invalid user admin from 1.2.3.4 port 64321 ssh2
Mar 15 14:35:01 server sshd[12417]: Failed password for invalid user admin from 192.168.100.50 port 65321 ssh2
Mar 15 15:00:01 server sshd[13001]: Connection closed by 192.168.1.1 port 22
Mar 15 15:01:01 server sshd[13002]: Accepted publickey for ubuntu from 10.0.0.1 port 22
Mar 15 15:02:01 server sshd[13003]: pam_unix(sshd:session): session opened for user ubuntu
Mar 15 15:03:01 server sshd[13004]: Received disconnect from 10.0.0.1 port 22
Mar 15 15:04:01 server sshd[13005]: Connection closed by 192.168.1.2 port 22
Mar 15 15:05:01 server sshd[13006]: Accepted password for admin from 10.0.0.2 port 22
Mar 15 15:06:01 server sshd[13007]: pam_unix(sshd:session): session opened for user admin
Mar 15 15:07:01 server sshd[13008]: Received disconnect from 10.0.0.2 port 22
Mar 15 15:08:01 server sshd[13009]: Connection closed by 192.168.1.3 port 22
Mar 15 15:09:01 server sshd[13010]: Accepted publickey for deploy from 10.0.0.3 port 22
Mar 15 15:10:01 server sshd[13011]: pam_unix(sshd:session): session opened for user deploy
Mar 15 15:11:01 server sshd[13012]: Received disconnect from 10.0.0.3 port 22
Mar 15 15:12:01 server sshd[13013]: Connection closed by 192.168.1.4 port 22
Mar 15 15:13:01 server sshd[13014]: Accepted publickey for jenkins from 10.0.0.4 port 22
Mar 15 15:14:01 server sshd[13015]: pam_unix(sshd:session): session opened for user jenkins
Mar 15 15:15:01 server sshd[13016]: Received disconnect from 10.0.0.4 port 22
Mar 15 15:16:01 server sshd[13017]: Connection closed by 192.168.1.5 port 22
Mar 15 15:17:01 server sshd[13018]: Accepted publickey for git from 10.0.0.5 port 22
Mar 15 15:18:01 server sshd[13019]: pam_unix(sshd:session): session opened for user git
Mar 15 15:19:01 server sshd[13020]: Received disconnect from 10.0.0.5 port 22
Mar 15 15:20:01 server sshd[13021]: Connection closed by 192.168.1.6 port 22
Mar 15 15:21:01 server sshd[13022]: Accepted publickey for www from 10.0.0.6 port 22
Mar 15 15:22:01 server sshd[13023]: pam_unix(sshd:session): session opened for user www
Mar 15 15:23:01 server sshd[13024]: Received disconnect from 10.0.0.6 port 22
Mar 15 15:24:01 server sshd[13025]: Connection closed by 192.168.1.7 port 22
Mar 15 15:25:01 server sshd[13026]: Accepted publickey for backup from 10.0.0.7 port 22
Mar 15 15:26:01 server sshd[13027]: pam_unix(sshd:session): session opened for user backup
Mar 15 15:27:01 server sshd[13028]: Received disconnect from 10.0.0.7 port 22
Mar 15 15:28:01 server sshd[13029]: Connection closed by 192.168.1.8 port 22
Mar 15 15:29:01 server sshd[13030]: Accepted publickey for monitor from 10.0.0.8 port 22
Mar 15 15:30:01 server sshd[13031]: pam_unix(sshd:session): session opened for user monitor
Mar 15 15:31:01 server sshd[13032]: Received disconnect from 10.0.0.8 port 22
Mar 15 15:32:01 server sshd[13033]: Connection closed by 192.168.1.9 port 22
Mar 15 15:33:01 server sshd[13034]: Accepted publickey for ansible from 10.0.0.9 port 22
Mar 15 15:34:01 server sshd[13035]: pam_unix(sshd:session): session opened for user ansible
Mar 15 15:35:01 server sshd[13036]: Received disconnect from 10.0.0.9 port 22
Mar 15 15:36:01 server sshd[13037]: Connection closed by 192.168.1.10 port 22
Mar 15 15:37:01 server sshd[13038]: Accepted publickey for puppet from 10.0.0.10 port 22
Mar 15 15:38:01 server sshd[13039]: pam_unix(sshd:session): session opened for user puppet
Mar 15 15:39:01 server sshd[13040]: Received disconnect from 10.0.0.10 port 22
Mar 15 15:40:01 server sshd[13041]: Connection closed by 192.168.1.11 port 22
Mar 15 15:41:01 server sshd[13042]: Accepted publickey for chef from 10.0.0.11 port 22
Mar 15 15:42:01 server sshd[13043]: pam_unix(sshd:session): session opened for user chef
Mar 15 15:43:01 server sshd[13044]: Received disconnect from 10.0.0.11 port 22
Mar 15 15:44:01 server sshd[13045]: Connection closed by 192.168.1.12 port 22
Mar 15 15:45:01 server sshd[13046]: Accepted publickey for salt from 10.0.0.12 port 22
Mar 15 15:46:01 server sshd[13047]: pam_unix(sshd:session): session opened for user salt
Mar 15 15:47:01 server sshd[13048]: Received disconnect from 10.0.0.12 port 22
Mar 15 15:48:01 server sshd[13049]: Connection closed by 192.168.1.13 port 22
Mar 15 15:49:01 server sshd[13050]: Accepted publickey for docker from 10.0.0.13 port 22
Mar 15 15:50:01 server sshd[13051]: pam_unix(sshd:session): session opened for user docker
Mar 15 15:51:01 server sshd[13052]: Received disconnect from 10.0.0.13 port 22
Mar 15 15:52:01 server sshd[13053]: Connection closed by 192.168.1.14 port 22
Mar 15 15:53:01 server sshd[13054]: Accepted publickey for kubernetes from 10.0.0.14 port 22
Mar 15 15:54:01 server sshd[13055]: pam_unix(sshd:session): session opened for user kubernetes
Mar 15 15:55:01 server sshd[13056]: Received disconnect from 10.0.0.14 port 22
Mar 15 15:56:01 server sshd[13057]: Connection closed by 192.168.1.15 port 22
Mar 15 15:57:01 server sshd[13058]: Accepted publickey for terraform from 10.0.0.15 port 22
Mar 15 15:58:01 server sshd[13059]: pam_unix(sshd:session): session opened for user terraform
Mar 15 15:59:01 server sshd[13060]: Received disconnect from 10.0.0.15 port 22
Mar 15 16:00:01 server sshd[13061]: Connection closed by 192.168.1.16 port 22
Mar 15 16:01:01 server sshd[13062]: Accepted publickey for vault from 10.0.0.16 port 22
Mar 15 16:02:01 server sshd[13063]: pam_unix(sshd:session): session opened for user vault
Mar 15 16:03:01 server sshd[13064]: Received disconnect from 10.0.0.16 port 22
Mar 15 16:04:01 server sshd[13065]: Connection closed by 192.168.1.17 port 22
Mar 15 16:05:01 server sshd[13066]: Accepted publickey for consul from 10.0.0.17 port 22
Mar 15 16:06:01 server sshd[13067]: pam_unix(sshd:session): session opened for user consul
Mar 15 16:07:01 server sshd[13068]: Received disconnect from 10.0.0.17 port 22
Mar 15 16:08:01 server sshd[13069]: Connection closed by 192.168.1.18 port 22
Mar 15 16:09:01 server sshd[13070]: Accepted publickey for nomad from 10.0.0.18 port 22
Mar 15 16:10:01 server sshd[13071]: pam_unix(sshd:session): session opened for user nomad
Mar 15 16:11:01 server sshd[13072]: Received disconnect from 10.0.0.18 port 22
Mar 15 16:12:01 server sshd[13073]: Connection closed by 192.168.1.19 port 22
Mar 15 16:13:01 server sshd[13074]: Accepted publickey for packer from 10.0.0.19 port 22
Mar 15 16:14:01 server sshd[13075]: pam_unix(sshd:session): session opened for user packer
Mar 15 16:15:01 server sshd[13076]: Received disconnect from 10.0.0.19 port 22
Mar 15 16:16:01 server sshd[13077]: Connection closed by 192.168.1.20 port 22
Mar 15 16:17:01 server sshd[13078]: Accepted publickey for vagrant from 10.0.0.20 port 22
Mar 15 16:18:01 server sshd[13079]: pam_unix(sshd:session): session opened for user vagrant
Mar 15 16:19:01 server sshd[13080]: Received disconnect from 10.0.0.20 port 22
Mar 15 16:20:01 server sshd[13081]: Connection closed by 192.168.1.21 port 22
Mar 15 16:21:01 server sshd[13082]: Accepted publickey for aws from 10.0.0.21 port 22
Mar 15 16:22:01 server sshd[13083]: pam_unix(sshd:session): session opened for user aws
Mar 15 16:23:01 server sshd[13084]: Received disconnect from 10.0.0.21 port 22
Mar 15 16:24:01 server sshd[13085]: Connection closed by 192.168.1.22 port 22
Mar 15 16:25:01 server sshd[13086]: Accepted publickey for gcp from 10.0.0.22 port 22
Mar 15 16:26:01 server sshd[13087]: pam_unix(sshd:session): session opened for user gcp
Mar 15 16:27:01 server sshd[13088]: Received disconnect from 10.0.0.22 port 22
Mar 15 16:28:01 server sshd[13089]: Connection closed by 192.168.1.23 port 22
Mar 15 16:29:01 server sshd[13090]: Accepted publickey for azure from 10.0.0.23 port 22
Mar 15 16:30:01 server sshd[13091]: pam_unix(sshd:session): session opened for user azure
Mar 15 16:31:01 server sshd[13092]: Received disconnect from 10.0.0.23 port 22
Mar 15 16:32:01 server sshd[13093]: Connection closed by 192.168.1.24 port 22
Mar 15 16:33:01 server sshd[13094]: Accepted publickey for digitalocean from 10.0.0.24 port 22
Mar 15 16:34:01 server sshd[13095]: pam_unix(sshd:session): session opened for user digitalocean
Mar 15 16:35:01 server sshd[13096]: Received disconnect from 10.0.0.24 port 22
Mar 15 16:36:01 server sshd[13097]: Connection closed by 192.168.1.25 port 22
Mar 15 16:37:01 server sshd[13098]: Accepted publickey for linode from 10.0.0.25 port 22
Mar 15 16:38:01 server sshd[13099]: pam_unix(sshd:session): session opened for user linode
Mar 15 16:39:01 server sshd[13100]: Received disconnect from 10.0.0.25 port 22
EOF

RUN chmod 644 /var/log/auth_attempts.log

CMD ["/bin/bash"]
