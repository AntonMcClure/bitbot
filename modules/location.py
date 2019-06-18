#--depends-on config

from src import ModuleManager, utils

URL_OPENCAGE = "https://api.opencagedata.com/geocode/v1/json"

class Module(ModuleManager.BaseModule):
    def on_load(self):
        self.exports.add("set", {"setting": "location",
            "help": "Set your location", "validate": self._get_location,
            "example": "London, GB"})

    def _get_location(self,  s):
        page = utils.http.request(URL_OPENCAGE, get_params={
            "q": s, "key": self.bot.config["opencagedata-api-key"], "limit": "1"
            }, json=True)
        if page and page.data["results"]:
            result = page.data["results"][0]
            timezone = result["annotations"]["timezone"]["name"]
            lat = result["geometry"]["lat"]
            lon = result["geometry"]["lng"]
            name = result["formatted"]

            return {"timezone": timezone, "lat": lat, "lon": lon, "name": name}
