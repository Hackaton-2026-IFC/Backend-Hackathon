from datetime import timedelta
import requests
from django.core.cache import cache
from django.utils import timezone
from rest_framework.exceptions import ValidationError

GEOCODE = 'https://geocoding-api.open-meteo.com/v1/search'
FORECAST = 'https://api.open-meteo.com/v1/forecast'

def forecast_for_task(task):
    if not task.clima_influencia:
        return {'disponivel': False, 'motivo': 'O clima não influencia nesta tarefa.'}
    target = task.prazo_antecipado or task.data_limite
    if not target:
        raise ValidationError({'data_limite': 'Defina uma data para consultar o clima.'})
    today = timezone.localdate()
    if target < today:
        return {'disponivel': False, 'motivo': 'A data já passou.'}
    if target > today + timedelta(days=15):
        return {'disponivel': False, 'motivo': 'Previsão ainda indisponível para esta data.'}
    location = task.localizacao.strip()
    if not location:
        raise ValidationError({'localizacao': 'Informe a localização.'})
    key = 'weather:v1:' + str(task.pk) + ':' + str(target) + ':' + location.casefold()
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        geo = requests.get(GEOCODE, params={'name': location, 'count': 1, 'language': 'pt', 'format': 'json'}, timeout=5)
        geo.raise_for_status()
        matches = geo.json().get('results') or []
        if not matches:
            raise ValidationError({'localizacao': 'Localização não encontrada. Utilize o nome da cidade.'})
        place = matches[0]
        params = {'latitude': place['latitude'], 'longitude': place['longitude'],
                  'daily': 'temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max',
                  'timezone': 'auto', 'start_date': target.isoformat(), 'end_date': target.isoformat()}
        weather = requests.get(FORECAST, params=params, timeout=7)
        weather.raise_for_status()
        daily = weather.json()['daily']
        result = {'disponivel': True, 'data': target.isoformat(),
                  'localizacao': {'nome': place['name'], 'pais': place.get('country'), 'estado': place.get('admin1')},
                  'temperatura_maxima_c': daily['temperature_2m_max'][0],
                  'temperatura_minima_c': daily['temperature_2m_min'][0],
                  'probabilidade_chuva_pct': daily['precipitation_probability_max'][0],
                  'vento_maximo_kmh': daily['wind_speed_10m_max'][0],
                  'fonte': 'Open-Meteo', 'aviso': 'Previsões podem mudar; não altera automaticamente o prazo.'}
        cache.set(key, result, timeout=3600)
        return result
    except (requests.Timeout, requests.ConnectionError, requests.HTTPError, KeyError, IndexError, ValueError) as exc:
        return {'disponivel': False, 'motivo': 'Serviço meteorológico indisponível. Tente novamente.'}
