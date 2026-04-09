"""
financial_service.py - Servicio de datos financieros usando Yahoo Finance API

Integra con Yahoo Finance API (RapidAPI) para obtener:
- Precio actual de acciones
- Market cap
- Rendimiento (1d, 5d, 1m, YTD)
- Volumen de trading

Cache: 24 horas por ticker (para no gastar los 500 requests/mes rápido)
"""

import json
import logging
import time
from typing import Dict, Optional

import requests

try:
    import config
except ImportError:
    from job_bot import config

try:
    from database import Database
except ImportError:
    from job_bot.database import Database

logger = logging.getLogger(__name__)

# TTL de cache: 24 horas (86400 segundos)
FINANCIAL_CACHE_TTL = 24 * 60 * 60

# Mapa de dominios a tickers (empresas populares)
DOMAIN_TO_TICKER = {
    # US Tech
    "google.com": "GOOGL",
    "apple.com": "AAPL",
    "microsoft.com": "MSFT",
    "amazon.com": "AMZN",
    "meta.com": "META",
    "facebook.com": "META",
    "netflix.com": "NFLX",
    "tesla.com": "TSLA",
    "nvidia.com": "NVDA",
    "adobe.com": "ADBE",
    "salesforce.com": "CRM",
    "oracle.com": "ORCL",
    "ibm.com": "IBM",
    "intel.com": "INTC",
    "amd.com": "AMD",
    "uber.com": "UBER",
    "lyft.com": "LYFT",
    "airbnb.com": "ABNB",
    "spotify.com": "SPOT",
    "zoom.us": "ZM",
    "slack.com": "WORK",  # Ahora es Salesforce
    "shopify.com": "SHOP",
    "squareup.com": "SQ",
    "block.xyz": "SQ",
    "coinbase.com": "COIN",
    "robinhood.com": "HOOD",
    "palantir.com": "PLTR",
    "snowflake.com": "SNOW",
    "datadoghq.com": "DDOG",
    "cloudflare.com": "NET",
    "twilio.com": "TWLO",
    "okta.com": "OKTA",
    "zscaler.com": "ZS",
    "crowdstrike.com": "CRWD",
    "sentinelone.com": "S",
    "mongodb.com": "MDB",
    "elastic.co": "ESTC",
    "confluent.io": "CFLT",
    "databricks.com": None,  # Privada
    "openai.com": None,  # Privada
    "anthropic.com": None,  # Privada
    "stripe.com": None,  # Privada
    
    # LATAM
    "mercadolibre.com": "MELI",
    "mercadolivre.com.br": "MELI",
    "nubank.com.br": "NU",
    "nubank.com": "NU",
    "inter.co": "INTR",  # Banco Inter
    "xpinc.com": "XP",
    "pagseguro.com.br": "PAGS",
    "stone.co": "STNE",
    "dlocal.com": "DLO",
    "globant.com": "GLOB",
    "despegar.com": "DESP",
    "pedidosya.com": None,  # Privada (Delivery Hero)
    "rapi.com": None,  # Privada
    "notco.com": None,  # Privada
    "Cornershop": None,  # Adquirida por Uber
    "Cornershop.com": None,  # Adquirida por Uber
    "trenesargentinos.com.ar": None,  # Estatal
    
    # Argentina (BYMA)
    "grupogalaxy.com": "GGAL",  # Grupo Financiero Galicia
    "bancogalicia.com.ar": "GGAL.BA",
    "bancogalicia.com": "GGAL",
    "bancolombia.com": "CIB",
    "itau.com.br": "ITUB",
    "itau.com": "ITUB",
    "santander.com.ar": "SAN.BA",
    "santander.com": "SAN",
    "bbva.com.ar": "BBVA.BA",
    "bbva.com": "BBVA",
    "icbc.com.ar": "ICBC.BA",
    "hsbc.com.ar": "HSBA.L",  # HSBC UK
    "macro.com.ar": "BMA.BA",
    "bancopatagonia.com.ar": "BPAT.BA",
    "supervielle.com.ar": "SUPV.BA",
    "credicoop.coop": None,  # Cooperativa, no cotiza
    "naranjax.com": None,  # Privada (Galicia)
    "uala.com.ar": None,  # Privada
    "uala.com": None,  # Privada
    "bna.com.ar": None,  # Banco Nación - estatal
    "ypf.com": "YPF",
    "ypf.com.ar": "YPF.BA",
    "tecpetrol.com.ar": "TECP.BA",  # Tecpetrol
    "cgcpower.com.ar": "CGPA2.BA",  # Central Puerto
    "edenor.com": "EDN",
    "edenor.com.ar": "EDN.BA",
    "edesur.com.ar": None,  # Enel
    "edelap.com.ar": "EDLPL.BA",
    "transportadora.com.ar": "TGSU2.BA",  # TGS
    "pampaenergia.com": "PAMP.BA",
    "centralpuerto.com": "CEPU2.BA",  # Central Puerto
    "aluar.com.ar": "ALUA.BA",
    "tenaris.com": "TS",
    "siderar.com": "ERAR.BA",  # Siderar
    "ternium.com": "TX",
    "acrecentar.com": "AGRO.BA",  # Agrofy
    "agrofy.com": None,  # Privada
    "bioceres.com": "BIOX",
    "molinos.com.ar": "MOLI.BA",
    "cresud.com": "CRESY",
    "cresud.com.ar": "CRES.BA",
    "irsa.com.ar": "IRSA.BA",
    "irsa.com": "IRS",
    "consultatio.com.ar": "CABA.BA",
    "bodegasbianchi.com.ar": "BOLT.BA",  # Bodegas Bianchi
    "longvie.com.ar": "LONG.BA",
    "mirgor.com.ar": "MIRG.BA",  # Mirgor
    "grupoclarin.com": "GCLA.BA",
    "clarin.com": "GCLA.BA",
    "cablevision.com.ar": "CVH.BA",  # Cablevisión Holding
    "telecom.com.ar": "TECO2.BA",  # Telecom Argentina
    "personal.com.ar": "TECO2.BA",  # Telecom
    "movistar.com.ar": "TEF",  # Telefónica España
    "arsat.com.ar": "ARS.BA",
    "rigeo.com.ar": "RIGO.BA",  # Rigolleau
    "garovagliozorra.com.ar": "GZC.BA",  # Garovaglio Zorraquin
    "bancoentrerios.com.ar": "BER.BA",  # Banco Entre Ríos
    "bancosanjuan.com.ar": "BSJ.BA",  # Banco San Juan
    "bancocredicoop.coop": None,  # Cooperativa
    "bancocomafi.com.ar": "COMA.BA",
    "bancohypo.com.ar": "BHIP.BA",  # Hipotecario
    "bancomacro.com.ar": "BMA.BA",
    
    # Otros
    "mercado.com.ar": None,  # Público
    "bolsadecereales.com.ar": None,
    "rofex.com.ar": None,
    "byma.com.ar": "BYMA.BA",  # Bolsas y Mercados Argentinos
}


def get_ticker_from_domain(domain: str) -> Optional[str]:
    """
    Obtiene el ticker de bolsa a partir del dominio de la empresa.
    
    Args:
        domain: Dominio (ej: "google.com")
    
    Returns:
        Ticker (ej: "GOOGL") o None si no se encuentra
    """
    if not domain:
        return None
    
    # Normalizar
    domain = domain.strip().lower()
    
    # Quitar www. si existe
    if domain.startswith("www."):
        domain = domain[4:]
    
    # Buscar match exacto
    if domain in DOMAIN_TO_TICKER:
        return DOMAIN_TO_TICKER[domain]
    
    # Buscar subdominios (ej: "careers.google.com" → "google.com")
    parts = domain.split(".")
    if len(parts) >= 2:
        # Probar con el dominio principal
        main_domain = ".".join(parts[-2:])
        if main_domain in DOMAIN_TO_TICKER:
            return DOMAIN_TO_TICKER[main_domain]
        
        # Para .com.ar, .co.uk, etc.
        if len(parts) >= 3:
            main_domain_with_tld = ".".join(parts[-3:])
            if main_domain_with_tld in DOMAIN_TO_TICKER:
                return DOMAIN_TO_TICKER[main_domain_with_tld]
    
    return None


def get_stock_data(ticker: str, db: Optional[Database] = None) -> Optional[Dict]:
    """
    Obtiene datos financieros de una acción por su ticker.
    
    1. Busca en cache local (24h TTL)
    2. Si no existe o expiró, consulta Yahoo Finance API
    3. Guarda en cache y retorna
    
    Args:
        ticker: Símbolo de la acción (ej: "MELI", "GOOGL")
        db: Instancia de Database (opcional)
    
    Returns:
        Dict con datos financieros o None
    """
    if not ticker:
        return None
    
    ticker = ticker.strip().upper()
    
    # Usar DB proporcionada o crear nueva
    if db is None:
        db = Database()
    
    # 1. Buscar en cache
    cached = _get_cached_stock_data(ticker, db)
    if cached:
        logger.info(f"[CACHE HIT] Stock data {ticker}")
        return cached
    
    # 2. Consultar API
    stock_data = _fetch_stock_from_api(ticker)
    
    if stock_data:
        # 3. Guardar en cache
        _cache_stock_data(ticker, stock_data, db)
        logger.info(f"[API FETCH] Stock {ticker} guardado en cache")
    
    return stock_data


def _get_cached_stock_data(ticker: str, db: Database) -> Optional[Dict]:
    """Recupera datos financieros del cache si son válidos."""
    import json
    
    row = db._fetchone(
        "SELECT data, cached_at FROM stock_data WHERE ticker = ?",
        (ticker,),
    )
    
    if not row:
        return None
    
    # Verificar TTL
    current_time = int(time.time())
    if current_time - row["cached_at"] > FINANCIAL_CACHE_TTL:
        return None
    
    try:
        return json.loads(row["data"])
    except json.JSONDecodeError:
        return None


def _cache_stock_data(ticker: str, data: Dict, db: Database):
    """Guarda datos financieros en cache."""
    import json
    
    current_time = int(time.time())
    data_json = json.dumps(data, ensure_ascii=False)
    
    try:
        db._execute(
            """INSERT OR REPLACE INTO stock_data 
               (ticker, data, cached_at) 
               VALUES (?, ?, ?)""",
            (ticker, data_json, current_time),
        )
    except Exception as e:
        logger.error(f"Error caching stock data for {ticker}: {e}")


def _fetch_stock_from_api(ticker: str) -> Optional[Dict]:
    """
    Consulta Yahoo Finance API para obtener datos de la acción.
    
    Usa el endpoint de quotes de Yahoo Finance 166 (RapidAPI).
    """
    if not config.RAPIDAPI_KEY:
        logger.warning("RAPIDAPI_KEY no configurada, no se pueden obtener datos financieros")
        return None
    
    # Yahoo Finance 166 API
    url = "https://yahoo-finance166.p.rapidapi.com/api/stock/get-chart"
    
    querystring = {
        "region": "US",
        "lang": "en",
        "symbol": ticker,
        "interval": "1d",
        "range": "1mo"
    }
    
    headers = {
        "X-RapidAPI-Key": config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": "yahoo-finance166.p.rapidapi.com"
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return _normalize_stock_response(data, ticker)
        
        elif response.status_code == 429:
            logger.warning(f"[RATE LIMIT] Yahoo Finance API para {ticker}")
            return None
        
        elif response.status_code == 404:
            logger.info(f"[NOT FOUND] Ticker {ticker} no encontrado")
            return None
        
        else:
            logger.warning(f"[API ERROR] {response.status_code} para {ticker}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning(f"[TIMEOUT] Consultando stock {ticker}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Consultando stock {ticker}: {e}")
        return None


def _normalize_stock_response(data: Dict, ticker: str) -> Optional[Dict]:
    """
    Normaliza la respuesta de Yahoo Finance a formato estándar.
    """
    try:
        # La respuesta de Yahoo Finance chart puede variar
        # Extraer datos del formato más común
        chart = data.get("chart", {})
        result = chart.get("result", [{}])[0] if chart.get("result") else {}
        
        if not result:
            return None
        
        meta = result.get("meta", {})
        timestamps = result.get("timestamp", [])
        prices = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
        
        if not prices:
            return None
        
        # Calcular rendimientos
        current_price = prices[-1] if prices else meta.get("regularMarketPrice", 0)
        prev_close = meta.get("previousClose", 0)
        week_ago_price = prices[0] if len(prices) > 5 else prev_close
        
        change_1d = 0
        if prev_close and current_price:
            change_1d = ((current_price - prev_close) / prev_close) * 100
        
        change_1w = 0
        if week_ago_price and current_price:
            change_1w = ((current_price - week_ago_price) / week_ago_price) * 100
        
        return {
            "ticker": ticker,
            "price": round(current_price, 2),
            "currency": meta.get("currency", "USD"),
            "market_cap": _format_market_cap(meta.get("marketCap")),
            "change_1d": round(change_1d, 2),
            "change_1w": round(change_1w, 2),
            "volume": meta.get("regularMarketVolume"),
            "prev_close": round(prev_close, 2),
            "exchange": meta.get("exchangeName", "N/A"),
            "timestamp": int(time.time())
        }
        
    except Exception as e:
        logger.error(f"Error normalizando respuesta para {ticker}: {e}")
        return None


def _format_market_cap(market_cap: Optional[int]) -> str:
    """Formatea market cap a formato legible (ej: $92.4B)."""
    if not market_cap:
        return "N/A"
    
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.1f}T"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.1f}B"
    elif market_cap >= 1e6:
        return f"${market_cap/1e6:.1f}M"
    else:
        return f"${market_cap:,.0f}"


def format_financial_section(stock_data: Dict, company_name: str = "") -> str:
    """
    Formatea los datos financieros para mostrar en Telegram con UX atractiva.
    """
    if not stock_data:
        return ""
    
    ticker = stock_data.get("ticker", "N/A")
    price = stock_data.get("price", 0)
    currency = stock_data.get("currency", "USD")
    market_cap = stock_data.get("market_cap", "N/A")
    change_1d = stock_data.get("change_1d", 0)
    change_1w = stock_data.get("change_1w", 0)
    volume = stock_data.get("volume")
    exchange = stock_data.get("exchange", "N/A")
    
    # Emoji según rendimiento
    def get_emoji(change):
        if change > 0:
            return "🟢"
        elif change < 0:
            return "🔴"
        return "⚪"
    
    # Formatear precio
    price_str = f"{price:,.2f}" if price else "N/A"
    
    # Formatear volumen
    volume_str = "N/A"
    if volume:
        if volume >= 1e6:
            volume_str = f"{volume/1e6:.1f}M"
        elif volume >= 1e3:
            volume_str = f"{volume/1e3:.1f}K"
        else:
            volume_str = f"{volume:,}"
    
    lines = [
        f"📊 FINANCIERO {'─' * 25}",
        f"📈 Ticker: <b>{ticker}</b> ({exchange})",
        f"💰 Precio: <b>{price_str} {currency}</b>",
    ]
    
    if market_cap != "N/A":
        lines.append(f"🏛️ Market Cap: {market_cap}")
    
    # Rendimientos con emojis
    day_emoji = get_emoji(change_1d)
    week_emoji = get_emoji(change_1w)
    
    sign_1d = "+" if change_1d > 0 else ""
    sign_1w = "+" if change_1w > 0 else ""
    
    lines.append(f"{day_emoji} Hoy: {sign_1d}{change_1d:.2f}%")
    lines.append(f"{week_emoji} Semana: {sign_1w}{change_1w:.2f}%")
    
    if volume_str != "N/A":
        lines.append(f"💹 Volumen: {volume_str}")
    
    # Agregar timestamp discretamente
    lines.append(f"\n<i>Actualizado: {time.strftime('%d/%m %H:%M')}</i>")
    
    return "\n".join(lines)


def format_company_full_message(company_data: Dict, stock_data: Optional[Dict] = None) -> str:
    """
    Formatea mensaje completo de empresa con datos financieros incluidos.
    UX premium con secciones bien definidas.
    """
    if not company_data:
        return "❌ No se encontró información de la empresa."
    
    name = company_data.get('name', 'N/A')
    domain = company_data.get('domain', 'N/A')
    description = company_data.get('description', '')
    industry = company_data.get('industry', 'N/A')
    size = company_data.get('company_size', company_data.get('employee_count', 'N/A'))
    location = company_data.get('location', 'N/A')
    website = company_data.get('website', f'https://{domain}')
    linkedin = company_data.get('linkedin_url', '')
    specialities = company_data.get('specialities', [])
    founded = company_data.get('founded', '')
    
    sections = []
    
    # Header con nombre prominente
    sections.append(f"🏢 <b>{name}</b>")
    sections.append(f"🌐 {domain}")
    sections.append("")
    
    # Sección financiera (si hay datos)
    if stock_data:
        financial_section = format_financial_section(stock_data, name)
        sections.append(financial_section)
        sections.append("")
    
    # Sección empresa
    sections.append(f"💼 EMPRESA {'─' * 26}")
    
    if description and description != "Sin descripción disponible":
        # Truncar descripción larga
        desc = description[:180] + "..." if len(description) > 180 else description
        sections.append(f"📝 {desc}")
        sections.append("")
    
    if industry and industry != "N/A":
        sections.append(f"🏷️ Industria: {industry}")
    
    if size and size != "N/A":
        sections.append(f"👥 Tamaño: {size}")
    
    if location and location != "N/A":
        sections.append(f"📍 Ubicación: {location}")
    
    if founded:
        sections.append(f"📅 Fundada: {founded}")
    
    if specialities and len(specialities) > 0:
        specs = ", ".join(specialities[:5])
        sections.append(f"✨ Especialidades: {specs}")
    
    sections.append("")
    
    # Links
    links = []
    if website:
        links.append(f"🔗 <a href='{website}'>Sitio web</a>")
    if linkedin:
        links.append(f"💼 <a href='{linkedin}'>LinkedIn</a>")
    if stock_data:
        ticker = stock_data.get("ticker")
        if ticker:
            yahoo_url = f"https://finance.yahoo.com/quote/{ticker}"
            links.append(f"📈 <a href='{yahoo_url}'>Yahoo Finance</a>")
    
    if links:
        sections.append(" • ".join(links))
    
    return "\n".join(sections)
