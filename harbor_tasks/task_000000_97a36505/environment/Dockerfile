FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/www/css && chmod 0777 /home/user && chmod 0755 /home/user/www && chmod 0755 /home/user/www/css

RUN cat <<'EOF' > /home/user/www/index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Static Site</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <h1>Welcome to my site</h1>
    <p>This is a simple static website.</p>
</body>
</html>
EOF

RUN cat <<'EOF' > /home/user/www/css/style.css
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
}

p {
    color: #666;
}
EOF

RUN chmod 0644 /home/user/www/index.html && chmod 0644 /home/user/www/css/style.css

WORKDIR /home/user

CMD ["/bin/bash"]
