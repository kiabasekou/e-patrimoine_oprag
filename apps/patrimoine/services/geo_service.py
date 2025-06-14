# services/geo_service.py
import requests
from django.conf import settings
from django.core.cache import cache

class GeoService:
    @staticmethod
    def geocoder_adresse(adresse, ville, pays="Gabon"):
        """Obtient les coordonnées GPS d'une adresse via une API externe"""
        # Construire la clé de cache
        cache_key = f"geo_coord_{adresse}_{ville}_{pays}"
        coordinates = cache.get(cache_key)
        
        if not coordinates:
            # Si pas en cache, appeler l'API
            api_key = settings.GEOCODING_API_KEY
            address_string = f"{adresse}, {ville}, {pays}"
            
            try:
                response = requests.get(
                    f"https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        'address': address_string,
                        'key': api_key
                    },
                    timeout=5
                )
                data = response.json()
                
                if data['status'] == 'OK' and data['results']:
                    location = data['results'][0]['geometry']['location']
                    coordinates = {
                        'latitude': location['lat'],
                        'longitude': location['lng'],
                        'formatted_address': data['results'][0]['formatted_address']
                    }
                    
                    # Mettre en cache pour 30 jours (adresses changent rarement)
                    cache.set(cache_key, coordinates, 30 * 24 * 60 * 60)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors du géocodage: {str(e)}")
                return None
        
        return coordinates