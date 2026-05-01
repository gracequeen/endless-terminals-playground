FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gawk \
    coreutils \
    grep \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/admin/data && chmod -R 0777 /home/user

# Create groups.dat (colon-delimited: gid:groupname:description)
RUN cat > /home/user/admin/data/groups.dat << 'GROUPSEOF'
1001:engineering:Engineering Department
1002:sales:Sales Department
1003:research:Research Department
1004:hr:Human Resources
1005:devops:DevOps Team
1006:finance:Finance Department
1007:marketing:Marketing Department
1008:interns:Intern Program
1009:security:Security Team
1010:support:Customer Support
1011:legal:Legal Department
1012:contractors:External Contractors
1013:executives:Executive Team
1014:facilities:Facilities Management
1015:it:IT Department
1016:qa:Quality Assurance
1017:design:Design Team
1018:analytics:Data Analytics
1019:compliance:Compliance Team
1020:training:Training Department
1021:procurement:Procurement Team
1022:operations:Operations Team
1023:product:Product Management
1024:partnerships:Business Partnerships
1025:communications:Communications Team
1026:strategy:Strategy Team
1027:innovation:Innovation Lab
1028:customer_success:Customer Success
1029:data_science:Data Science Team
1030:infrastructure:Infrastructure Team
1031:mobile:Mobile Development
1032:web:Web Development
1033:backend:Backend Development
1034:frontend:Frontend Development
1035:database:Database Administration
1036:networking:Network Engineering
1037:cloud:Cloud Services
1038:automation:Automation Team
1039:testing:Testing Team
1040:documentation:Documentation Team
1041:localization:Localization Team
1042:accessibility:Accessibility Team
1043:performance:Performance Team
1044:reliability:Site Reliability
1045:architecture:Architecture Team
1046:platform:Platform Team
1047:integrations:Integrations Team
1048:api:API Team
1049:sdk:SDK Team
1050:tools:Developer Tools
GROUPSEOF

# Generate users.dat, emails.dat, and memberships.dat with Python
RUN python3 << 'PYTHONEOF'
import random
import os

random.seed(42)

# Generate 800 unique usernames
first_names = ['james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'joseph', 'thomas', 'charles',
               'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara', 'susan', 'jessica', 'sarah', 'karen',
               'daniel', 'matthew', 'anthony', 'mark', 'donald', 'steven', 'paul', 'andrew', 'joshua', 'kenneth',
               'nancy', 'betty', 'margaret', 'sandra', 'ashley', 'dorothy', 'kimberly', 'emily', 'donna', 'michelle',
               'brian', 'george', 'edward', 'ronald', 'timothy', 'jason', 'jeffrey', 'ryan', 'jacob', 'gary',
               'lisa', 'helen', 'samantha', 'katherine', 'christine', 'deborah', 'rachel', 'laura', 'carolyn', 'janet',
               'kevin', 'eric', 'stephen', 'larry', 'justin', 'scott', 'brandon', 'raymond', 'frank', 'benjamin',
               'amanda', 'stephanie', 'nicole', 'melissa', 'rebecca', 'debra', 'sharon', 'cynthia', 'kathleen', 'amy',
               'alex', 'chris', 'jordan', 'taylor', 'morgan', 'casey', 'jamie', 'drew', 'pat', 'sam',
               'anna', 'emma', 'olivia', 'sophia', 'isabella', 'mia', 'charlotte', 'amelia', 'harper', 'evelyn']

last_names = ['smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller', 'davis', 'rodriguez', 'martinez',
              'hernandez', 'lopez', 'gonzalez', 'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin',
              'lee', 'perez', 'thompson', 'white', 'harris', 'sanchez', 'clark', 'ramirez', 'lewis', 'robinson',
              'walker', 'young', 'allen', 'king', 'wright', 'scott', 'torres', 'nguyen', 'hill', 'flores',
              'green', 'adams', 'nelson', 'baker', 'hall', 'rivera', 'campbell', 'mitchell', 'carter', 'roberts',
              'gomez', 'phillips', 'evans', 'turner', 'diaz', 'parker', 'cruz', 'edwards', 'collins', 'reyes',
              'stewart', 'morris', 'morales', 'murphy', 'cook', 'rogers', 'gutierrez', 'ortiz', 'morgan', 'cooper',
              'peterson', 'bailey', 'reed', 'kelly', 'howard', 'ramos', 'kim', 'cox', 'ward', 'richardson',
              'watson', 'brooks', 'chavez', 'wood', 'james', 'bennett', 'gray', 'mendoza', 'ruiz', 'hughes',
              'price', 'alvarez', 'castillo', 'sanders', 'patel', 'myers', 'long', 'ross', 'foster', 'jimenez',
              'powell', 'jenkins', 'perry', 'russell', 'sullivan', 'bell', 'coleman', 'butler', 'henderson', 'barnes',
              'gonzales', 'fisher', 'vasquez', 'simmons', 'stokes', 'yang', 'conner', 'chen', 'wong', 'kumar']

shells = ['/bin/bash', '/bin/zsh', '/bin/sh', '/usr/bin/fish', '/bin/tcsh']
shell_weights = [60, 20, 10, 7, 3]

primary_gids = list(range(1001, 1011))

usernames = set()
# Add required users first
usernames.add('aconner')
usernames.add('zyang')

while len(usernames) < 800:
    fn = random.choice(first_names)
    ln = random.choice(last_names)
    # Various username formats
    fmt = random.choice([
        f"{fn[0]}{ln}",
        f"{fn}{ln[0]}",
        f"{fn}.{ln}",
        f"{fn}_{ln}",
        f"{ln}{fn[0]}",
        f"{fn}{random.randint(1,99)}"
    ])
    if len(fmt) <= 20 and fmt not in usernames:
        usernames.add(fmt)

usernames = sorted(list(usernames))

# Assign UIDs - make sure aconner=1042 and zyang=1799
uid_map = {}
available_uids = list(range(1001, 1801))
available_uids.remove(1042)
available_uids.remove(1799)
random.shuffle(available_uids)

for username in usernames:
    if username == 'aconner':
        uid_map[username] = 1042
    elif username == 'zyang':
        uid_map[username] = 1799
    else:
        uid_map[username] = available_uids.pop()

# Assign primary GIDs - aconner=1001, zyang=1003
gid_map = {}
for username in usernames:
    if username == 'aconner':
        gid_map[username] = 1001
    elif username == 'zyang':
        gid_map[username] = 1003
    else:
        gid_map[username] = random.choice(primary_gids)

# Assign shells - aconner=/bin/bash, zyang=/bin/zsh
shell_map = {}
for username in usernames:
    if username == 'aconner':
        shell_map[username] = '/bin/bash'
    elif username == 'zyang':
        shell_map[username] = '/bin/zsh'
    else:
        shell_map[username] = random.choices(shells, weights=shell_weights)[0]

# Generate GECOS (full name)
gecos_map = {}
for username in usernames:
    fn = random.choice(first_names).capitalize()
    ln = random.choice(last_names).capitalize()
    gecos_map[username] = f"{fn} {ln}"

# Write users.dat (sorted alphabetically by username)
with open('/home/user/admin/data/users.dat', 'w') as f:
    for username in sorted(usernames):
        uid = uid_map[username]
        gid = gid_map[username]
        gecos = gecos_map[username]
        homedir = f"/home/{username}"
        shell = shell_map[username]
        f.write(f"{username}|{uid}|{gid}|{gecos}|{homedir}|{shell}\n")

# Write emails.dat (sorted numerically by UID - this is different from users.dat sort order!)
uid_to_username = {v: k for k, v in uid_map.items()}
with open('/home/user/admin/data/emails.dat', 'w') as f:
    for uid in sorted(uid_to_username.keys()):
        username = uid_to_username[uid]
        email = f"{username}@corp.local"
        f.write(f"{uid}\t{email}\n")

# Assign supplementary groups
# aconner: 1001, 1005, 1012 (engineering, devops, contractors)
# zyang: 1003, 1008 (research, interns)
supp_groups = {}
all_gids = list(range(1001, 1051))
for username in usernames:
    uid = uid_map[username]
    if username == 'aconner':
        supp_groups[uid] = [1001, 1005, 1012]
    elif username == 'zyang':
        supp_groups[uid] = [1003, 1008]
    else:
        # Random 1-5 supplementary groups including primary
        primary = gid_map[username]
        num_extra = random.randint(0, 4)
        extras = random.sample([g for g in all_gids if g != primary], num_extra)
        supp_groups[uid] = sorted([primary] + extras)

# Write memberships.dat (sorted by UID)
with open('/home/user/admin/data/memberships.dat', 'w') as f:
    for uid in sorted(supp_groups.keys()):
        groups = ' '.join(str(g) for g in supp_groups[uid])
        f.write(f"{uid} {groups}\n")

print("Data files generated successfully")
PYTHONEOF

# Create the buggy export_users.sh script
RUN cat > /home/user/admin/export_users.sh << 'SCRIPTEOF'
#!/bin/bash
# export_users.sh - Export user data to CSV format
# Combines data from multiple source files

DATA_DIR="/home/user/admin/data"
OUTPUT_FILE="/home/user/admin/export.csv"

# Source files
USERS_DAT="$DATA_DIR/users.dat"
EMAILS_DAT="$DATA_DIR/emails.dat"
GROUPS_DAT="$DATA_DIR/groups.dat"
MEMBERSHIPS_DAT="$DATA_DIR/memberships.dat"

# Create temporary directory
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Write header
echo "username,uid,primary_group,email,shell,supplementary_groups" > "$OUTPUT_FILE"

# Extract and sort user data (sorted alphabetically by username)
sort -t'|' -k1,1 "$USERS_DAT" > "$TMPDIR/users_sorted.tmp"

# Extract emails - BUG 1: using space delimiter instead of tab
# emails.dat is tab-delimited but we use cut -d' ' (space)
cut -d' ' -f1 "$EMAILS_DAT" | sort -n > "$TMPDIR/email_uids.tmp"
cut -d' ' -f2 "$EMAILS_DAT" | sort -n > "$TMPDIR/emails.tmp"

# BUG 2: Sorting mismatch - users are sorted alphabetically, but we're pasting
# with emails sorted by UID numerically. The paste will combine wrong lines.
# We sort users by username but emails by uid, so line N of users doesn't
# correspond to line N of emails.

# Extract uid from users for joining
awk -F'|' '{print $2}' "$TMPDIR/users_sorted.tmp" > "$TMPDIR/user_uids.tmp"

# Create email lookup by uid (but this still has the delimiter bug)
sort -t' ' -k1,1n "$EMAILS_DAT" > "$TMPDIR/emails_sorted.tmp"

# Process each user
while IFS='|' read -r username uid gid gecos homedir shell; do
    # Get email for this uid - BUG 1 manifests here: the cut with wrong delimiter
    # causes the whole "uid<TAB>email" to be treated as field 1
    email=$(grep "^${uid}" "$TMPDIR/emails_sorted.tmp" | cut -d' ' -f2)

    # If email is empty (because cut -d' ' failed), fall back to the broken paste method
    if [ -z "$email" ]; then
        # This creates even more chaos - just use a placeholder
        email=$(awk -v u="$uid" '$1 == u {print $2}' "$EMAILS_DAT")
    fi

    # Resolve primary group name - BUG 3: awk uses wrong field separator
    # groups.dat is colon-delimited but awk defaults to space/tab
    # so the whole "gid:groupname:description" becomes $1
    primary_group=$(awk -v g="$gid" '$1 == g {print $2}' "$GROUPS_DAT")

    # If group resolution failed, just use the gid
    if [ -z "$primary_group" ]; then
        primary_group="$gid"
    fi

    # Get supplementary groups for this uid
    supp_gids=$(grep "^${uid} " "$MEMBERSHIPS_DAT" | cut -d' ' -f2-)

    # Resolve supplementary group names - BUG 3 again: wrong FS in awk
    supp_names=""
    for sgid in $supp_gids; do
        gname=$(awk -v g="$sgid" '$1 == g {print $2}' "$GROUPS_DAT")
        if [ -z "$gname" ]; then
            gname="$sgid"
        fi
        if [ -z "$supp_names" ]; then
            supp_names="$gname"
        else
            supp_names="$supp_names;$gname"
        fi
    done

    # Output CSV line
    echo "$username,$uid,$primary_group,$email,$shell,$supp_names"

done < "$TMPDIR/users_sorted.tmp" >> "$OUTPUT_FILE"

exit 0
SCRIPTEOF

RUN chmod +x /home/user/admin/export_users.sh

RUN chmod -R 0777 /home/user/admin
