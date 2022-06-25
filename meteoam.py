# -*- coding: utf-8 -*-

import collections
from datetime import datetime
import json
import requests
import re

from bs4 import BeautifulSoup

class Weather:
    _from_url = {
        "coperto.png": 0,
        "coperto_foschia.png": 1,
        "coperto_nebbia.png": 2,
        "coperto_neve.png": 3,
        "coperto_pioggia.png": 4,
        "coperto_temporale.png": 5,
        "foschia.png": 6,
        "fumo.png": 7,
        "molto_nuvoloso.png": 8,
        "molto_nuvoloso_foschia.png": 9,
        "molto_nuvoloso_nebbia.png": 10,
        "molto_nuvoloso_neve.png": 11,
        "molto_nuvoloso_pioggia.png": 12,
        "molto_nuvoloso_temporale.png": 13,
        "nebbia.png": 14,
        "neve.png": 15,
        "nuvoloso.png": 16,
        "nuvoloso_foschia.png": 17,
        "nuvoloso_nebbia.png": 18,
        "nuvoloso_neve.png": 19,
        "nuvoloso_pioggia.png": 20,
        "nuvoloso_temporale.png": 21,
        "pioggia.png": 22,
        "poco_nuvoloso.png": 23,
        "poco_nuvoloso_foschia.png": 24,
        "poco_nuvoloso_nebbia.png": 25,
        "poco_nuvoloso_neve.png": 26,
        "poco_nuvoloso_pioggia.png": 27,
        "poco_nuvoloso_temporale.png": 28,
        "sabbia.png": 29,
        "sabbia_polvere.png": 30,
        "sereno.png": 31,
        "sereno_foschia.png": 32,
        "sereno_nebbia.png": 33,
        "sereno_neve.png": 34,
        "sereno_pioggia.png": 35,
        "sereno_temporale.png": 36,
        "sollevamento_neve.png": 37,
        "temporale.png": 38
    }
    w_id = -1
    def __init__(self, url):
        self.w_id = self._from_url[url.split("/")[-1]]
    
    def to_text(self):
        return ["Coperto","Coperto con foschia","Coperto con nebbia","Coperto con neve","Coperto con pioggia","Coperto con temporali","Foschia","Fumo","Molto nuvoloso","Molto nuvoloso con foschia","Molto nuvoloso con nebbia","Molto nuvoloso con neve","Molto nuvoloso con pioggia","Molto nuvoloso con temporali","Nebbia","Neve","Nuvoloso","Nuvoloso con foschia","Nuvoloso con nebbia","Nuvoloso con neve","Nuvoloso con pioggia","Nuvoloso con temporali","Pioggia","Poco nuvoloso","Poco nuvoloso con foschia","Poco nuvoloso con nebbia","Poco nuvoloso con neve","Poco nuvoloso con pioggia","Poco nuvoloso con temporali","Sabbia","Sabbia e polvere","Sereno","Sereno con foschia","Sereno con nebbia","Sereno con neve","Sereno con pioggia","Sereno con temporali","Sollevamento neve","Temporali"][self.w_id]

class MeteoAM:
    place_id = None
    def __init__(self, place):
        if type(place) is str:
            # Ottengo un ID che mi permette di cercare il nome della localita
            response = requests.request("GET", "http://www.meteoam.it/ajaxblocks", params={"blocks":"ricerca_localita-ricerca_previsioni_localita_hp","nocache":"1","path":"ta/previsione/0/"}, headers={'User-Agent': 'pymeteoam'})
            soup = BeautifulSoup(json.loads(response.text)["ricerca_localita-ricerca_previsioni_localita_hp"]["content"], 'html.parser')
            token = soup.find_all(attrs={"name": "form_build_id"})[0]["value"]
            # Effettuo la ricerca
            response = requests.request("GET", "http://www.meteoam.it/ricerca_localita/autocomplete/" + place, headers={'User-Agent': 'pymeteoam'})
            localita = json.loads(response.text, object_pairs_hook=collections.OrderedDict)
            nome = list(localita.values())[0]
            response = requests.request("POST", "http://www.meteoam.it/ta/previsione/", data="ricerca_localita="+list(localita.keys())[0]+"&form_id=ricerca_localita_form&form_build_id="+token, headers={'content-type': 'application/x-www-form-urlencoded', 'User-Agent': 'pymeteoam'}, allow_redirects=False)
            self.place_id = response.headers["Location"].split('/')[-2]
        else:
            self.place_id = place

    def forecast_24h(self):
        response = requests.request("GET", "http://www.meteoam.it/sites/all/modules/custom/tempo_in_atto/highcharts/dati_temperature_giornaliero.php", data=0, params={"icao":str(self.place_id)}, headers={'User-Agent': 'pymeteoam'})
        press_cond = response.text
        response = requests.request("GET", "http://www.meteoam.it/sites/all/modules/custom/tempo_in_atto/highcharts/dati_temperature.php", data=0, params={"id":str(self.place_id)}, headers={'User-Agent': 'pymeteoam'})
        temp = response.text
        dati_meteo_grezzi = ([f+g for f,g in zip(temp.replace("\r", '').split("\n"), ["\t"+"\t".join(h.split("\t")[1:]) for h in press_cond.replace("\r", '').split("\n")])])[:-1]
        return [(lambda x: {"date": datetime.strptime(x[0], "%m/%d/%Y %H:%M"), "temperature": float(x[1]), "pressure": float(x[2]), "weather": Weather(x[3]).to_text()})(dta.split("\t")) for dta in dati_meteo_grezzi]

    def forecast_daily(self):
        dow = {"Lun": 1, "Mar": 2, "Mer": 3, "Gio": 4, "Ven": 5, "Sab": 6, "Dom": 0}
        response = requests.request("GET", "http://www.meteoam.it/widget/localita/"+str(self.place_id), headers={'User-Agent': 'pymeteoam'})
        soup = BeautifulSoup(response.text, 'html.parser')
        return {
            "place": soup.find("h3").find("a").text.capitalize(), "forecast": [(lambda x: {"day_of_week": dow[x[0].text], "weather": x[1].find("img")["alt"], "min_t": float(x[2].text.replace("°",'')), "max_t": float(x[3].text.replace("°",'')), "wind": {"knots": x[4].find(attrs={"class":"badge"}).text, "direction": x[4].find_all("span")[0]["class"][0].replace("vento" ,"")}})(r.find_all("td")) for r in soup.find_all("tr")[1:]]}

    def prob_rain_today(self):
        response = requests.request("GET", "http://www.meteoam.it/ta/previsione/" + str(self.place_id), headers={'User-Agent': 'pymeteoam'})
        soup = BeautifulSoup(response.text, 'html.parser')
        temp = soup.find_all("tr")
        max_pct = 0
        last_hour = 0
        for t in temp:
            hour = re.search("[0-9][0-9]:[0-9][0-9]", str(t))
            if(hour):
               current_hour = int((hour.string[9:11]))
               #controllo che questo dato di pioggia non sia del giorno successivo
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
