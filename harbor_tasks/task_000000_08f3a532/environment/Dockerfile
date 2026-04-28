FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/i18n-server/locales && chmod -R 0777 /home/user/i18n-server

WORKDIR /home/user/i18n-server

RUN python3 -m venv /home/user/i18n-server/venv

RUN /home/user/i18n-server/venv/bin/pip install flask pyyaml

RUN cat > /home/user/i18n-server/config.yaml << 'EOF'
port: 5050
locale_dir: locales
default_locale: en
supported_locales:
  - en
  - fr
  - de
EOF

RUN cat > /home/user/i18n-server/locales/en.yaml << 'EOF'
greeting: "Hello"
farewell: "Goodbye"
EOF

RUN cat > /home/user/i18n-server/locales/fr.yaml << 'EOF'
greeting: "Bonjour"
farewell: "Au revoir"
EOF

RUN printf 'greeting:\t"Hallo"\nfarewell: Auf Wiedersehen: formal\n' > /home/user/i18n-server/locales/de.yaml

RUN cat > /home/user/i18n-server/app.py << 'APPEOF'
from flask import Flask, request, jsonify
import yaml
import os

app = Flask(__name__)

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

def load_locale(locale_name):
    """Load a locale file and return its contents as a dict."""
    locale_dir = os.path.join(os.path.dirname(__file__), config['locale_dir'])
    locale_file = os.path.join(locale_dir, f'{locale_name}.yaml')

    if not os.path.exists(locale_file):
        return None

    try:
        with open(locale_file, 'r') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        app.logger.error(f"failed to load locale: {locale_name}")
        return None

@app.route('/api/v1/translate')
def translate():
    locale = request.args.get('locale', config['default_locale'])
    key = request.args.get('key')

    if not key:
        return jsonify({'error': 'key parameter required'}), 400

    if locale not in config['supported_locales']:
        return jsonify({'error': f'unsupported locale: {locale}'}), 400

    locale_data = load_locale(locale)

    if locale_data is None:
        return jsonify({'error': 'failed to load locale'}), 500

    if key not in locale_data:
        return jsonify({'error': f'key not found: {key}'}), 404

    return jsonify({'translation': locale_data[key]})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['port'])
APPEOF

RUN chmod -R 0777 /home/user/i18n-server

WORKDIR /home/user

CMD ["/bin/bash"]
