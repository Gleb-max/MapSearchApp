import requests
from .toponym import Toponym, Organisation


class ApiInteraction:
    GEOCODE_API_SERVER = "http://geocode-maps.yandex.ru/1.x/"
    MAP_API_SERVER = "http://static-maps.yandex.ru/1.x/"

    def get_geocode(self, toponym, **kwargs):
        geocode_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": toponym,
            "format": "json"
        }
        geocode_params.update(kwargs)
        response = requests.get(self.GEOCODE_API_SERVER, params=geocode_params)
        if not response:
            return None
        json_response = response.json()
        toponyms = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not toponyms:
            return None
        return Toponym(toponyms[0]["GeoObject"])

    def get_geocodes(self, toponym, **kwargs):
        geocode_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": toponym,
            "format": "json"
        }
        geocode_params.update(kwargs)
        response = requests.get(self.GEOCODE_API_SERVER, params=geocode_params)
        if not response:
            return None
        json_response = response.json()
        toponyms = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not toponyms:
            return []
        return toponyms

    def get_image(self, coordinates, map_type, scale, label=None):
        map_params = {
            "ll": coordinates,
            "l": map_type,
            "z": scale,
        }
        if label is not None:
            map_params["pt"] = ",".join(map(str, label)) + ",pm2rdm"
        response = requests.get(self.MAP_API_SERVER, params=map_params)
        if not response or response.status_code in [400, 404]:
            return None
        return response.content

    def get_organisation(self, coords, text, **kwargs):
        search_url = "https://search-maps.yandex.ru/v1/"
        search_params = {
            "apikey": "82616f09-03e3-4c0e-b00e-5fb29f5fcbdd",
            "lang": "ru_RU",
            "text": text,
            "ll": ",".join(map(str, coords))
        }
        search_params.update(kwargs)

        response = requests.get(search_url, search_params)
        if response is None:
            return None
        json_response = response.json()
        organisations = json_response["features"]
        if not organisations:
            return None
        return Organisation(organisations[0])
