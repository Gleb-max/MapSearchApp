class Toponym:
    def __init__(self, data):
        self.data = data

    def getCoordinates(self):
        return self.data["Point"]["pos"].replace(" ", ",")

    def getCountry(self):
        return self.data["metaDataProperty"]["GeocoderMetaData"]["AddressDetails"]["Country"]

    def getAddress(self):
        return self.getCountry()["AddressLine"]

    def getDeltaLongitude(self):
        envelope = self.data["boundedBy"]["Envelope"]
        upLong = float(envelope["upperCorner"].split()[0])
        downLong = float(envelope["lowerCorner"].split()[0])
        return upLong - downLong

    def getDeltaLatitude(self):
        envelope = self.data["boundedBy"]["Envelope"]
        upLat = float(envelope["upperCorner"].split()[1])
        downLat = float(envelope["lowerCorner"].split()[1])
        return upLat - downLat

    def getScale(self):
        envelope = self.data["boundedBy"]["Envelope"]
        up = list(map(float, envelope["upperCorner"].split()))
        down = list(map(float, envelope["lowerCorner"].split()))
        dx = up[0] - down[0]
        dy = up[1] - down[1]
        return f"{dx},{dy}"

    def getPostalCode(self):
        try:
            return self.getCountry()["AdministrativeArea"]["Locality"][
                "Thoroughfare"]["Premise"]["PostalCode"]["PostalCodeNumber"]
        except KeyError:
            return None
