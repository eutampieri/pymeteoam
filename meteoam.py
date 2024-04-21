# -*- coding: utf-8 -*-

import collections
from datetime import datetime
import json
import requests

from bs4 import BeautifulSoup


class Weather:
    _from_icon_id = {
        "01": "Sereno giorno",
        "02": "Parzialmente velato giorno",
        "03": "Velato",
        "04": "Poco nuvoloso giorno",
        "05": "Molto nuvoloso giorno",
        "06": "Coperto",
        "07": "Coperto",
        "08": "Pioggia debole",
        "09": "Pioggia forte",
        "10": "Temporale",
        "11": "Pioggia mista a neve",
        "12": "Pioggia che gela",
        "13": "Foschia giorno",
        "14": "Nebbia",
        "15": "Grandine",
        "16": "Neve",
        "17": "Tromba d’aria o marina",
        "18": "Fumo",
        "19": "Tempesta di sabbia",
        "31": "Sereno notte",
        "32": "Parzialmente Velato notte",
        "34": "Poco nuvoloso notte",
        "35": "Molto nuvoloso notte",
        "36": "Foschia notte",
    }
    w_id = None

    def __init__(self, id):
        self.w_id = id

    def to_text(self):
        return self._from_icon_id[self.w_id]


class MeteoAM:
    lat = None
    lon = None

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def _get_data(self):
        return requests.get(f"https://api.meteoam.it/deda-meteograms/api/GetMeteogram/preset1/{self.lat},{self.lon}", headers={
                'User-Agent': 'pymeteoam'}).json()

    def forecast_24h(self):
        data = self._get_data()

        hourly_data = []
        for i, ts in enumerate(data["timeseries"]):
            datapoint = {"timestamp": ts}
            for j, p in enumerate(data["paramlist"]):
                datapoint[p] = data["datasets"]["0"][str(j)][str(i)]
            hourly_data.append(datapoint)

        return [
            (
                lambda x: {
                    "date": datetime.fromisoformat(
                        x["timestamp"]),
                    "rain": x["tpp"],
                    "humidity": x["r"],
                    "wind": {"direction": x["wdir"], "speed": x["wkmh"]},
                    "temperature": x["2t"],
                    "pressure": x["pmsl"],
                    "weather": Weather(
                        x["icon"]).to_text()})(
                dta) for dta in hourly_data]

    def forecast_daily(self):
        data = self._get_data()
        day_by_day = []
        for x in data["extrainfo"]["stats"]:
            if x["icon"] == '-':
                continue
            day_by_day.append(x)

        return {"place": (self.lat, self.lon),
                "forecast": [(lambda x: {"date": datetime.fromisoformat(x["localDate"]),
                                         "day_of_week": datetime.fromisoformat(x["localDate"]).weekday(),
                                         "weather": Weather(x["icon"]).to_text(),
                                         "min_t": x["minCelsius"],
                                         "max_t": x["maxCelsius"],
                                        })(r) for r in day_by_day]}

    def prob_rain_today(self):
        raise NotImplementedError("This function is not yet compatible with the new MeteoAM. You'll find the hourly probabilities in the hourly forecast")
        response = requests.request("GET",
                                    "http://www.meteoam.it/ta/previsione/" + str(self.place_id),
                                    headers={'User-Agent': 'pymeteoam'})
        soup = BeautifulSoup(response.text, 'html.parser')
        temp = soup.find_all("tr")
        max_pct = 0
        last_hour = 0
        for t in temp:
            hour = re.search("[0-9][0-9]:[0-9][0-9]", str(t))
            if(hour):
                current_hour = int((hour.string[9:11]))
                # controllo che questo dato di pioggia non sia del giorno
                # successivo
                if(last_hour > current_hour):
                    return(max_pct)
                last_hour = current_hour
            td = t.find_all("td")
            if(len(td)):
                rain = re.search("[0-9]*%", str(td[1]))
                if(rain):
                    r = int(rain.string[4:-6])
                    if(max_pct < r):
                        max_pct = r
        return(max_pct)
