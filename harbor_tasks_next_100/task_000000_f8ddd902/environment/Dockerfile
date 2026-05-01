FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    mosquitto \
    mosquitto-clients \
    curl \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest aiohttp aiomqtt

RUN mkdir -p /home/user/edge-gateway/logs && \
    chmod -R 0777 /home/user

RUN cat > /home/user/edge-gateway/gateway.py << 'ENDOFFILE'
import asyncio
from aiohttp import web
import aiomqtt

mqtt_client = None

async def health_handler(request):
    if mqtt_client and mqtt_client._client.is_connected():
        return web.json_response({"status": "healthy", "mqtt": "connected"})
    return web.json_response({"status": "degraded", "mqtt": "disconnected"}, status=503)

async def sensor_handler(request):
    data = await request.json()
    if mqtt_client:
        await mqtt_client.publish("sensors/data", str(data))
    return web.json_response({"accepted": True})

def create_app():
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_post('/sensor', sensor_handler)
    return app

async def mqtt_loop():
    global mqtt_client
    async with aiomqtt.Client("localhost", 1883) as client:
        mqtt_client = client
        async for message in client.messages:
            print(f"Received: {message.payload}")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Start MQTT in background
    loop.create_task(mqtt_loop())

    # Run HTTP server - THIS IS THE BUG
    # web.run_app() creates its own event loop by default when called without loop=
    # and blocks the current thread, never yielding to the mqtt_loop task
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8080, print=lambda x: open('/home/user/edge-gateway/logs/gateway.log', 'a').write(x + '\n'))

if __name__ == '__main__':
    main()
ENDOFFILE

RUN cat > /home/user/edge-gateway/start.sh << 'ENDOFFILE'
#!/bin/bash
cd /home/user/edge-gateway

# Start mosquitto in background
mosquitto -d

# Wait for mosquitto to be ready
sleep 1

# Run the gateway
python3 gateway.py
ENDOFFILE

RUN chmod +x /home/user/edge-gateway/start.sh && \
    chmod 0777 /home/user/edge-gateway/gateway.py && \
    chmod 0777 /home/user/edge-gateway/logs

WORKDIR /home/user

CMD ["/bin/bash"]
