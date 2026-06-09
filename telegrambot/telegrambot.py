from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging, os, asyncio, aiomysql, traceback, locale, json
import matplotlib.pyplot as plt
from io import BytesIO
import paho.mqtt.publish as publish

token=os.environ["TB_TOKEN"]

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)

import paho.mqtt.client as mqtt

# Esta es la memoria del bot. Arranca vacía hasta que la placa hable.
estado_placa = {
    "setpoint": "Esperando...",
    "periodo": "Esperando...",
    "modo": "Esperando...",
    "rele": "Esperando..."
}

# --- FUNCIONES DEL ESCUCHADOR MQTT ---
def al_conectar(client, userdata, flags, rc):
    # Cuando el bot arranca, se suscribe al instante al tópico de la placa
    client.subscribe("los_masones")
    logging.info("Bot suscrito a 'los_masones' en segundo plano")

def al_recibir_mensaje(client, userdata, msg):
    global estado_placa
    try:
        # Decodificamos el mensaje y lo pasamos a JSON
        payload = msg.payload.decode('utf-8')
        datos = json.loads(payload)
        
        # Si el JSON tiene los datos, los guardamos en la memoria del bot
        if "Setpoint" in datos:
            estado_placa["setpoint"] = datos["Setpoint"]
        if "Periodo" in datos:
            estado_placa["periodo"] = datos["Periodo"]
        if "Modo" in datos:
            estado_placa["modo"] = datos["Modo"]
        if "rele" in datos:
            estado_placa["rele"] = datos["rele"]
            
    except Exception as e:
        # Si llega algo que no es JSON (ej: la palabra "on" del relé), lo ignora sin crashear
        pass

async def mandar_comando_mqtt(topico, mensaje):
    """
    Se conecta rápidamente a Mosquitto, manda un mensaje y se desconecta.
    Ideal para eventos de botones rápidos.
    """
    try:
        # Recuperamos las contraseñas que ya tenés en tu .env
        usuario = os.environ.get("MQTT_USR")
        password = os.environ.get("MQTT_PASS")
        #servidor = os.environ.get("SERVIDOR", "mosquitto")
        servidor = "mosquitto" 
        publish.single(
            topic=topico,
            payload=mensaje,
            hostname=servidor,
            port=1883, 
            auth={'username': usuario, 'password': password}
        )
        logging.info(f"MQTT Publicado exitosamente -> {topico} : {mensaje}")
        
    except Exception as e:
        logging.error(f"Fallo al publicar MQTT en {topico}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("se conectó: " + str(update.message.from_user.id))
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    kb = [["temperatura"],["humedad"],["gráfico temperatura"],["gráfico humedad"],["Destello"]]
    await context.bot.send_message(update.message.chat.id, text="Bienvenido al Bot "+ nombre + " " + apellido,reply_markup=ReplyKeyboardMarkup(kb))

async def comando_periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificamos si escribieron exactamente 2 argumentos después de /setpoint
    if len(context.args) == 2 and context.args[0] == '@editar':
        nuevo_valor = context.args[1]
        
        # Filtro de seguridad: ¿Es realmente un número entero?
        if nuevo_valor.isdigit():
            # Armamos el JSON como lo espera tu placa
            datos = {"msg": nuevo_valor}
            payload_json = json.dumps(datos)
            
            # Mandamos el MQTT
            await mandar_comando_mqtt("los_masones/periodo", payload_json)
            await context.bot.send_message(update.message.chat.id, text=f"✅ Periodo actualizado a {nuevo_valor}")
        else:
            # Si escribieron letras en vez de números
            await context.bot.send_message(update.message.chat.id, text="⚠️ El valor debe ser un número (ejemplo: /periodo @editar 25)")


async def comando_setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificamos si escribieron exactamente 2 argumentos después de /setpoint
    if len(context.args) == 2 and context.args[0] == '@editar':
        nuevo_valor = context.args[1]
        
        # Filtro de seguridad: ¿Es realmente un número entero?
        if nuevo_valor.isdigit():
            # Armamos el JSON como lo espera tu placa
            datos = {"msg": nuevo_valor}
            payload_json = json.dumps(datos)
            
            # Mandamos el MQTT
            await mandar_comando_mqtt("los_masones/setpoint", payload_json)
            await context.bot.send_message(update.message.chat.id, text=f"✅ Setpoint actualizado a {nuevo_valor}")
        else:
            # Si escribieron letras en vez de números
            await context.bot.send_message(update.message.chat.id, text="⚠️ El valor debe ser un número (ejemplo: /setpoint @editar 25)")
            
    # Si mandaron solo /setpoint o le pifiaron al formato
    else:
        # Nota: Si estás guardando el setpoint actual en MariaDB, podrías hacer un SELECT acá para mostrarlo.
        mensaje_ayuda = (
            "Para modificar el setpoint, usá el siguiente formato:\n"
            "`/setpoint @editar <numero>`\n"
            "Ejemplo: `/setpoint @editar 25`"
        )
        # parse_mode='Markdown' permite que el texto entre tildes invertidas se vea como código en Telegram
        await context.bot.send_message(update.message.chat.id, text=mensaje_ayuda, parse_mode='Markdown')

async def consultar_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        f"📊 **Estado Actual de la Placa:**\n\n"
        f"🎯 Setpoint: {estado_placa['setpoint']}\n"
        f"⏱️ Periodo: {estado_placa['periodo']} seg\n"
        f"⚙️ Modo: {estado_placa['modo']}\n"
        f"⚙️ rele: {estado_placa['rele']}\n"

    )
    await context.bot.send_message(update.message.chat.id, text=texto)

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para el curso de IoT FIO")

async def rele(update: Update, context):
    logging.info(context.args)
    if context.args and context.args[0] == '@on':
        await context.bot.send_message(update.message.chat.id, text="¡Encendido!")
        datos = {
        "msg": "on"
        }
        payload_json = json.dumps(datos)
        await mandar_comando_mqtt("los_masones/rele", payload_json)
    elif context.args and context.args[0] == '@off':
        await context.bot.send_message(update.message.chat.id, text="¡Apagado!")

        datos = {
        "msg": "off"
        }
        payload_json = json.dumps(datos)
        await mandar_comando_mqtt("los_masones/rele", payload_json)
    else:
        await context.bot.send_message(update.message.chat.id, text="Por favor, use @on o @off")

async def modo(update: Update, context):
    logging.info(context.args)
    if context.args and context.args[0] == '@auto':
        await context.bot.send_message(update.message.chat.id, text="El rele paso a modo automático")
        datos = {
        "msg": "auto"
        }
        payload_json = json.dumps(datos)
        await mandar_comando_mqtt("los_masones/modo", payload_json)
    elif context.args and context.args[0] == '@manual':
        await context.bot.send_message(update.message.chat.id, text="El rele paso a modo manual!")

        datos = {
        "msg": "manual"
        }
        payload_json = json.dumps(datos)
        await mandar_comando_mqtt("los_masones/modo", payload_json)
    else:
        await context.bot.send_message(update.message.chat.id, text="Por favor, use @auto o @manual")


async def accionar_destello(update: Update, context):
    
    datos = {
        "msg": "on"
    }
    payload_json = json.dumps(datos)
    
    await mandar_comando_mqtt("los_masones/destello", payload_json)
    
    await context.bot.send_message(
        update.message.chat.id, 
        text="¡Señal enviada! La placa está destellando 🔦"
    )


async def medicion(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text} FROM mediciones ORDER BY timestamp DESC LIMIT 1"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        r = await cur.fetchone()
        if update.message.text == 'temperatura':
            unidad = 'ºC'
        else:
            unidad = '%'
        await context.bot.send_message(update.message.chat.id,
                                    text="La última {} es de {} {},\nregistrada a las {:%H:%M:%S %d/%m/%Y}"
                                    .format(update.message.text, str(r[1]).replace('.',','), unidad, r[0]))
        logging.info("La última {} es de {} {}, medida a las {:%H:%M:%S %d/%m/%Y}".format(update.message.text, r[1], unidad, r[0]))
    conn.close()

async def graficos(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text.split()[1]} FROM mediciones where id mod 2 = 0 AND timestamp >= NOW() - INTERVAL 1 DAY ORDER BY timestamp"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        filas = await cur.fetchall()

        fig, ax = plt.subplots(figsize=(7, 4))
        fecha,var=zip(*filas)
        ax.plot(fecha,var)
        ax.grid(True, which='both')
        ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
        ax.set_xlabel('fecha')
        ax.set_ylabel('unidad')

        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        buffer.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
    conn.close()

def main():
    # --- 1. ARRANCAR EL ESCUCHADOR MQTT EN SEGUNDO PLANO ---
    cliente_escucha = mqtt.Client()
    cliente_escucha.username_pw_set(os.environ.get("MQTT_USR"), os.environ.get("MQTT_PASS"))
    cliente_escucha.on_connect = al_conectar
    cliente_escucha.on_message = al_recibir_mensaje
    
    # Se conecta (usamos "mosquitto" fijo por la red interna)
    cliente_escucha.connect("mosquitto", 1883, 60)
    cliente_escucha.loop_start() # ESTA ES LA MAGIA QUE LO MANDA A SEGUNDO PLANO

    # --- 2. ARRANCAR TELEGRAM ---
    application = Application.builder().token(token).build()
    
    # ... acá van todos tus handlers que ya tenés (start, acercade, graficos...) ...
    application.add_handler(CommandHandler('consultar', consultar_estado)) # Tu comando nuevo
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(MessageHandler(filters.Regex("^Destello$"), accionar_destello))
    application.add_handler(CommandHandler('rele', rele))
    application.add_handler(CommandHandler('modo', modo))
    application.add_handler(CommandHandler('periodo', comando_periodo))
    application.add_handler(CommandHandler('setpoint', comando_setpoint))
    application.add_handler(MessageHandler(filters.Regex("^(temperatura|humedad)$"), medicion))
    application.add_handler(MessageHandler(filters.Regex("^(gráfico temperatura|gráfico humedad)$"), graficos))
    application.run_polling()

if __name__ == '__main__':
    main()
