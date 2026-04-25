#LIBRERIAS 
import discord
from discord.ext import commands
import os
import requests
from google.cloud import dialogflow_v2 as dialogflow
from dotenv import load_dotenv
import wikipedia
wikipedia.set_lang("es")
from urllib.parse import quote
import asyncio
import urllib.parse
import random
import json
import aiohttp

#CONFIGURACIÓN 
load_dotenv("contraseñas.env")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credenciales.json"
TOKEN = os.getenv('TOKEN_DISCORD')
CLIMA_API_KEY = os.getenv('CLIMA_API_ID')
PROYECT_KEY = os.getenv("PROJECT_ID")
OPENAQ_KEY = os.getenv("OPENAQ_KEY_API")
CARBONFOOTPRIN_KEY = os.getenv("CARBONFOOTPRINT_ID")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
session_client = dialogflow.SessionsClient()

with open("informacion.json", "r", encoding="utf-8") as f:
    datos_json = json.load(f)

#GLOBALES
alternativas_pendientes = {}
#----FUNCIONES----

#Detecta intents en dialogflow
def detectar_intent(texto, session_id):
    session = session_client.session_path(PROYECT_KEY, session_id)
    query_input = { "text": { "text": texto, "language_code": "es"} }
    response = session_client.detect_intent( request={"session": session, "query_input": query_input} )
    return response.query_result

#Mensaje informativo del bot
async def get_ecopingudata(message, resultado):
    respuesta = resultado.fulfillment_text
    await message.channel.send(respuesta)

#Intent info meteorologica de ciudades
def get_clima(ciudad, pais):
    paises_iso = {
        "argentina": "AR", "bolivia": "BO", "brasil": "BR", "canadá": "CA", "chile": "CL",
        "colombia": "CO", "costa rica": "CR", "cuba": "CU", "ecuador": "EC", "el salvador": "SV",
        "estados unidos": "US", "guatemala": "GT", "honduras": "HN", "méxico": "MX", "nicaragua": "NI",
        "panamá": "PA", "paraguay": "PY", "perú": "PE", "puerto rico": "PR", "república dominicana": "DO",
        "uruguay": "UY", "venezuela": "VE", "alemania": "DE", "austria": "AT", "bélgica": "BE", "dinamarca": "DK", "españa": "ES",
        "francia": "FR", "grecia": "GR", "holanda": "NL", "países bajos": "NL", "irlanda": "IE",
        "italia": "IT", "noruega": "NO", "polonia": "PL", "portugal": "PT", "reino unido": "GB",
        "inglaterra": "GB", "rusia": "RU", "suecia": "SE", "suiza": "CH", "turquía": "TR","australia": "AU", 
        "china": "CN", "corea del sur": "KR", "egipto": "EG", "india": "IN",
        "japón": "JP", "marruecos": "MA", "nueva zelanda": "NZ", "sudáfrica": "ZA"
    }
    
    ciudad_limpia = str(ciudad).strip()
    pais_limpio = str(pais).strip().lower()
    codigo_pais = paises_iso.get(pais_limpio, pais_limpio) 

    busqueda = f"{ciudad_limpia},{codigo_pais}" if codigo_pais else ciudad_limpia
    query_encoded = urllib.parse.quote(busqueda)

    url_geo = f"http://api.openweathermap.org/geo/1.0/direct?q={query_encoded}&limit=1&appid={CLIMA_API_KEY}"
    
    print(f"DEBUG URL: {url_geo}") 
    
    try:
        res_geo = requests.get(url_geo).json()
        if not res_geo:
            return "No encontré la ubicación."
        
        d = res_geo[0]
        lat, lon = d['lat'], d['lon']
        url_clima = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={CLIMA_API_KEY}&units=metric&lang=es"
        res_clima = requests.get(url_clima, timeout=10)
        data = res_clima.json()

        url_aire = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={CLIMA_API_KEY}"
        res_aire = requests.get(url_aire, timeout=10).json()
        
        aqi = res_aire["list"][0]["main"]["aqi"]
        aqi_dict = {1: "Excelente ✅", 2: "Buena 🟢", 3: "Moderada 🟡", 4: "Pobre 🟠", 5: "Muy Pobre 🔴"}
        calidad_aire = aqi_dict.get(aqi, "Sin datos")

        if res_clima.status_code != 200:
            return "Error al conectar con el servicio de clima."

        temp = round(data["main"]["temp"])
        desc = data["weather"][0]["description"]
        humedad = data["main"]["humidity"]
        temp_max = data["main"]["temp_max"]
        temp_min = data["main"]["temp_min"]
        presion = data["main"]["pressure"]
        nubes = data["clouds"]["all"]
        viento = data["wind"]["speed"]

        return (
            f"🌡️ **Clima en {ciudad}:**\n"
            f"• Temperatura : {temp}°C, {desc}\n"
            f"• Aire: **{calidad_aire}**\n"
            f"• Humedad: {humedad}% | Mín: {temp_min}°C / Máx: {temp_max}°C\n"
            f"• Presión: {presion} hPa\n"
            f"• Viento: {viento} m/s\n"
            f"• Nubes: {nubes}%\n" 
        )
    except Exception as e:
        print(f"Error en get_clima: {e}")
        return "Hubo un error al procesar el clima. 🐧"

#Intent info definiciones de conceptos 
async def get_definicion(termino):
    try:
        pagina = wikipedia.page(termino, auto_suggest=True)
        
        resultado = wikipedia.summary(termino, sentences=2, auto_suggest=True)
        resultado = " ".join(resultado.split())

        if len(resultado) > 400:
            resultado = resultado[:397].rstrip() + "..."
            
        return f"{resultado}\n\nSi quieres saber más visita: {pagina.url}"
        
    except wikipedia.exceptions.DisambiguationError as e:
        opciones = e.options[:3]
        return f"El término es ambiguo. ¿Te refieres a: {', '.join(opciones)}?"
    
    except (wikipedia.exceptions.PageError, KeyError):
        return f"No encontré información sobre '{termino}'."
    
    except Exception as e:
        print(f"Error log: {e}") 
        return "Lo siento, ocurrió un error inesperado."

#Intent info dato curioso de contaminacion, recursos y reciclaje
async def get_dato_curioso(tema):
    if tema == "contaminacion":
        lista = datos_json["datos_curiosos_contaminacion"]
    elif tema == "recursos":
        lista = datos_json["datos_uso_recursos"]
    else:
        lista = datos_json["datos_curiosos_reciclaje"]
    
    frase = random.choice(lista)
    return {"fulfillmentText": f"¡Claro! ¿Sabías que? {frase} 🌍🐧"}

async def get_alternativas_productos(categoria_producto):
    try:
        alternativas = datos_json["alternativas"]
    
        cat_buscada = str(categoria_producto).strip().lower()
        print(f"2. Buscando coincidencias para: '{cat_buscada}'")

        coincidencias = [
            alt for alt in alternativas 
            if str(alt.get("categoria", "")).strip().lower() == cat_buscada
        ]

        print(f"3. Número de coincidencias: {len(coincidencias)}")

        if not coincidencias:
            return f"Por ahora no tengo alternativas para '{categoria_producto}'. 🐧", []

        # 3. Elección
        producto = random.choice(coincidencias)
        restantes = [p for p in coincidencias if p != producto]
        
        print(f"4. Producto elegido: {producto.get('proveedor')}")

        texto_respuesta = (
            f"🌿 **Proveedor:** {producto.get('proveedor', 'N/A')}\n"
            f"🛒 **Vende:** {producto.get('vende', 'N/A')}\n"
            f"📝 **Info:** {producto.get('info', 'N/A')}\n"
            f"🔗 **URL:** {producto.get('url', 'N/A')}\n\n"
        )

        if restantes:
            texto_respuesta += f"Tengo {len(restantes)} opciones más. ¿Quieres ver otra?"
        else:
            texto_respuesta += "Es la única opción que tengo por ahora."

        return texto_respuesta, restantes

    except Exception as e:
        # Esto te dirá exactamente qué falló en la terminal
        print(f"💥 ERROR CRÍTICO EN LA FUNCIÓN: {e}")
        return "Lo siento, tuve un problema al procesar la lista de productos. 🐧", []

async def get_consejo(tipo):
    try:
        lista_categorias = datos_json.get("consumo_responsable", [])
        
        categoria_encontrada = next((item for item in lista_categorias if item["categoria"] == tipo), None)

        if not categoria_encontrada:
            return f"Aún estoy aprendiendo consejos sobre '{tipo}', pero pronto tendré más. 🐧"

        consejo_final = random.choice(categoria_encontrada["consejos"])
        
        return f"💡 **Tip de Consumo Responsable:**\n{consejo_final} 🌍"

    except Exception as e:
        return "Ups, se me olvidó ese consejo por un segundo. ¡Inténtalo de nuevo! 🐧"
    

    URL = f"https://api.emissions.dev/v1/freight/emissions"
    headers = {"Authorization": f"Bearer {CARBONFOOTPRIN_KEY}","Content-Type": "application/json"}

    print(headers)
    data = {
        "origin": origen,
        "destination": destino,
        "mode": modo,
        "weight_kg": peso_kg
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=headers, json=data) as resp:
            if resp.status == 200:
                result = await resp.json()
                co2 = result.get("co2e_kg")
                distancia = result.get("distance_km")
                return (
                    f"🌍 Tu envío de {peso_kg} kg desde {origen} hasta {destino} "
                    f"en {modo} genera **{co2:.2f} kg CO₂e** en {distancia:.0f} km."
                )
            else:
                print(f"Error API: {resp.status}") # Esto sale en tu terminal
                return "❌ Error al calcular: verifica que las ciudades o el modo sean válidos. 🐧"

async def get_manualidad(tipo):
    tipo = tipo.lower() 
    lista = datos_json.get(tipo)

    if not lista:
        return {"fulfillmentText": "Lo siento, no encontré manualidades para ese tipo. 🐧"}

    manualidad = random.choice(lista)
    return {
        "fulfillmentText": (
            f"✨ Idea: {manualidad['nombre']} 🐧\n"
            f"Materiales: {', '.join(manualidad['materiales'])}\n"
            f"Cómo hacerlo: {manualidad['informacion']}"
            + (f"\nMira en: {manualidad['url']}" if manualidad["url"] else "")
        )
    }

@bot.event
async def on_ready():
    print(f'Pingu conectado como {bot.user.name} 🌍🐧') 

async def get_ecopingudata(message, resultado):
    respuesta = resultado.fulfillment_text
    await message.channel.send(respuesta)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() in ["sí", "si", "ver otra", "otra"]:
        if message.author.id in alternativas_pendientes:
            data = alternativas_pendientes[message.author.id]
            if data["lista"]:
                producto = data["lista"].pop(0) 
                msg = f"🌿 **Proveedor:** {producto['proveedor']}\n🔗 **URL:** {producto['url']}"
                await message.channel.send(msg)
                return 

    ctx = await bot.get_context(message)
    if ctx.valid:
        await bot.process_commands(message)
        return
    
    resultado = detectar_intent(message.content, str(message.author.id))
    intent_nombre = resultado.intent.display_name
    params = dict(resultado.parameters)

    if intent_nombre == "get_ecopingudata":
        await get_ecopingudata(message, resultado)
    
    elif intent_nombre == "get_clima":
        def limpiar(dato):
            if not dato: return ""
            if hasattr(dato, "__iter__") and not isinstance(dato, str):
                return str(dato[0]) if len(dato) > 0 else ""
            return str(dato)

        ciudad_limpia = limpiar(params.get("geo-city"))
        pais_limpio = limpiar(params.get("geo-country"))
        reporte = await asyncio.to_thread(get_clima, ciudad_limpia, pais_limpio)
        
        await message.channel.send(reporte)

    elif intent_nombre == "get_definicion":
        valor = resultado.parameters.get('termino')
        resumen = await get_definicion(valor)
        await message.channel.send(resumen, suppress_embeds=True)

    elif intent_nombre == "get_dato_curioso":
        tema_detectado = params.get("tema") 
        respuesta_dict = await get_dato_curioso(tema_detectado)
        
        await message.channel.send(respuesta_dict["fulfillmentText"])

    elif intent_nombre == "get_alternativas_productos":
        categoria_param = params.get("categoria_producto") # Usa el diccionario params que ya extrajiste arriba
        
        if categoria_param:
            print("📦 Categoría detectada:", categoria_param)
            respuesta, restantes = await get_alternativas_productos(categoria_param)
            
            await message.channel.send(respuesta)
    
            if restantes:
                alternativas_pendientes[message.author.id] = {
                    "categoria": categoria_param,
                    "lista": restantes
                }
        else:
            await message.channel.send("No entendí de qué producto hablas 😅")

    elif intent_nombre == "get_consejo":
        valor_tipo = params.get("tipo") 
        
        if valor_tipo:
            respuesta_consejo = await get_consejo(valor_tipo)
            await message.channel.send(respuesta_consejo)
        else:
            temas = ["comida", "hogar", "energia", "reciclaje"]
            respuesta_random = await get_consejo(random.choice(temas))
            await message.channel.send(f"No especificaste un tema, pero aquí tienes uno general:\n{respuesta_random}")

    elif intent_nombre == "get_huella_carbono":
        embed_link = (
            "🌱 **Calcula tu Huella de Carbono**\n\n"
            "Para obtener un resultado preciso y visual, te recomiendo usar esta calculadora profesional:\n"
            "👉 https://www.footprintcalculator.org/home/es \n\n"
            "¡Cuando termines, cuéntame cuántos planetas salieron! 🌎"
        )
        await message.channel.send(embed_link)
            
    elif intent_nombre == "get_manualidad":
        tipo_detectado = params.get("tipo") 
        respuesta_dict = await get_manualidad(tipo_detectado)
        await message.channel.send(respuesta_dict["fulfillmentText"])


    elif resultado.fulfillment_text:
        await message.channel.send(resultado.fulfillment_text)

bot.run(TOKEN)
