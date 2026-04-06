from gen_ai_hub.proxy.core.proxy_clients import get_proxy_client
client = get_proxy_client()                                                                                                          
client.deployments    
for d in client.deployments:
    print(vars(d))    