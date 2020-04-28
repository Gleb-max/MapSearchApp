import requests
from .toponym import Toponym


class ApiInteraction:
    GEOCODE_API_SERVER = "http://geocode-maps.yandex.ru/1.x/"
    MAP_API_SERVER = "http://static-maps.yandex.ru/1.x/"

    def get_geocode(self, toponym):
        geocode_params = {
            "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
            "geocode": toponym,
            "format": "json"
        }
        response = requests.get(self.GEOCODE_API_SERVER, params=geocode_params)
        if not response:
            return None
        json_response = response.json()
        toponyms = json_response["response"]["GeoObjectCollection"]["featureMember"]
        if not toponyms:
            return None
        return Toponym(toponyms[0]["GeoObject"])

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
