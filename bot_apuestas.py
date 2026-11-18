import telebot
import requests

TELEGRAM_TOKEN = '8884589605:AAE8Ti67Vhw7-JPrKZK3CSXQnP1nHR4BHik'
ODDS_API_KEY = '043b604b50d8519fcd730946f3aa53a4'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Casa de referencia "Sharp" (la más precisa). Suele ser Pinnacle.
CASA_REFERENCIA = 'Pinnacle' 
# Margen de valor mínimo esperado para que el bot lo considere una "Recomendación" (ej: 5% de ventaja)
MARGEN_VALUE_MINIMO = 1.05 

def buscar_recomendaciones(deporte):
    url = f'https://api.the-odds-api.com/v4/sports/{deporte}/odds'
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'eu,us',  
        'markets': 'h2h',    
        'oddsFormat': 'decimal'
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return "❌ Error al conectar con la API."
        
    data = response.json()
    if not data:
        return "⚠️ No hay eventos disponibles en este momento."

    recomendaciones = f"🎯 *RECOMENDACIONES DE APUESTA (VALUEBETS) - {deporte}*\n\n"
    encontro_oportunidad = False
    
    # Iteramos sobre los partidos
    for partido in data:
        cuotas_pinnacle = {}
        
        # 1. Primero, buscamos las cuotas de la casa de referencia (Pinnacle)
        for bookmaker in partido['bookmakers']:
            if bookmaker['title'] == CASA_REFERENCIA:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            cuotas_pinnacle[outcome['name']] = outcome['price']
                break # Ya encontramos Pinnacle para este partido

        # Si el partido no está en Pinnacle, lo saltamos, porque no tenemos contra qué comparar
        if not cuotas_pinnacle:
            continue

        # 2. Comparamos las demás casas contra Pinnacle
        for bookmaker in partido['bookmakers']:
            casa_actual = bookmaker['title']
            if casa_actual == CASA_REFERENCIA: continue # No comparamos Pinnacle consigo mismo
            
            for market in bookmaker['markets']:
                if market['key'] == 'h2h':
                    for outcome in market['outcomes']:
                        equipo = outcome['name']
                        cuota_ofrecida = outcome['price']
                        cuota_real = cuotas_pinnacle.get(equipo, 0)
                        
                        # 3. La Matemática del Valor (Valuebet)
                        # Si la casa X paga considerablemente más que Pinnacle, es un error de la casa X.
                        if cuota_real > 0:
                            # Calculamos si la cuota ofrecida supera nuestro margen de ventaja sobre la "real"
                            ventaja = cuota_ofrecida / cuota_real 
                            
                            if ventaja >= MARGEN_VALUE_MINIMO:
                                encontro_oportunidad = True
                                porcentaje_valor = round((ventaja - 1) * 100, 2)
                                
                                recomendaciones += f"🏟️ *{partido['home_team']} vs {partido['away_team']}*\n"
                                recomendaciones += f"🔥 *Recomendación:* Apostar a **{equipo}**\n"
                                recomendaciones += f"💰 **Dónde apostar:** {casa_actual}\n"
                                recomendaciones += f"📈 Cuota ofrecida: {cuota_ofrecida}\n"
                                recomendaciones += f"📉 Cuota real (Pinnacle): {cuota_real}\n"
                                recomendaciones += f"📊 *Valor matemático (Edge): {porcentaje_valor}%*\n"
                                recomendaciones += "--------------------------\n"

    if not encontro_oportunidad:
        return f"😔 No encontré recomendaciones de valor (Valuebets) en este momento para {deporte} con un margen mayor al {(MARGEN_VALUE_MINIMO-1)*100}%. Las casas están ajustadas."
        
    return recomendaciones

@bot.message_handler(commands=['nba_recomendaciones'])
def comando_nba_value(message):
    bot.reply_to(message, "Analizando el mercado NBA en busca de errores en las casas de apuestas... 🤖🏀")
    resultado = buscar_recomendaciones('basketball_nba')
    bot.send_message(message.chat.id, resultado, parse_mode="Markdown")

@bot.message_handler(commands=['futbol_recomendaciones'])
def comando_futbol_value(message):
    bot.reply_to(message, "Cruzando datos de La Liga contra Pinnacle buscando valor... 🤖⚽")
    resultado = buscar_recomendaciones('soccer_spain_la_liga')
    bot.send_message(message.chat.id, resultado, parse_mode="Markdown")

bot.polling()