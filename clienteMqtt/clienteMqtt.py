import asyncio
import os
import logging
import aiomqtt
from aiomqtt import TLSParameters

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(taskName)s] - %(levelname)s: %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S %z'
)

async def sms(client, topic_escucha):
    """Escucha mensajes en el Tópico 2."""
    async for message in client.messages:
        logging.info(f"Recibido en {topic_escucha}: {message.payload.decode()}")

async def contador(cont):
    """Suma 1 al contador cada 3 segundos."""
    while True:
        await asyncio.sleep(3)
        cont["valor"] += 1
        logging.info(f"Contador: {cont['valor']}")

async def publicacion(client, topic_publica, cont):
    """Envía el contador por el Tópico 1 cada 5 segundos."""
    while True:
        await asyncio.sleep(5)
        await client.publish(topic_publica, payload=str(cont["valor"]))
        logging.info(f"Publicado en {topic_publica}: {cont['valor']}")

async def main():
    
    server = os.environ['SERVIDOR']
    t_publica = os.environ['TOPICO_1'] 
    t_escucha = os.environ['TOPICO_2']

    cont = {"valor": 0}

    try:
        async with aiomqtt.Client(server, port=8883, tls_params=TLSParameters()) as client:
            await client.subscribe(t_escucha) 
            
            async with asyncio.TaskGroup() as tg:
                tg.create_task(sms(client, t_escucha), name="Escucha")
                tg.create_task(contador(cont), name="Incrementador")
                tg.create_task(publicacion(client, t_publica, cont), name="Publicador")

    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("Buen intento")

if __name__ == "__main__":
    asyncio.run(main())