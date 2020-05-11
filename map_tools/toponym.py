class Toponym:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return super().__str__() + f" (Address: {self.getAddress()})"

    def getCoordinates(self):
        return tuple(map(float, self.data["Point"]["pos"].split()))

    def getCountry(self):
        return self.data["metaDataProperty"]["GeocoderMetaData"]["AddressDetails"]["Country"]

    def getAddress(self):
        return self.getCountry()["AddressLine"]

    def getName(self):
        return self.getAddress()

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
            try:
                return self.getCountry()["AdministrativeArea"]["SubAdministrativeArea"]["Locality"][
                    "Thoroughfare"]["Premise"]["PostalCode"]["PostalCodeNumber"]
            except KeyError:
                return None


class Organisation:
    def __init__(self, data):
        self.data = data
        self.postal_code = None

    def __str__(self):
        return super().__str__() + f" (Address: {self.getAddress()})"

    def getCoordinates(self):
        return tuple(self.data["geometry"]["coordinates"])

    def getProperties(self):
        return self.data["properties"]["CompanyMetaData"]

    def getName(self):
        return self.getProperties()["name"]

    def getAddress(self):
        return self.getProperties()["address"]

    def getDeltaLongitude(self):
        upLong = self.data["properties"]["boundedBy"][1][0]
        downLong = self.data["properties"]["boundedBy"][0][0]
        return upLong - downLong

    def getDeltaLatitude(self):
        upLat = self.data["properties"]["boundedBy"][1][1]
        downLat = self.data["properties"]["boundedBy"][0][1]
        return upLat - downLat

    def getScale(self):
        up = self.data["properties"]["boundedBy"][1]
        down = self.data["properties"]["boundedBy"][0]
        dx = up[0] - down[0]
        dy = up[1] - down[1]
        return f"{dx},{dy}"

    def getPostalCode(self):
        return self.postal_code
