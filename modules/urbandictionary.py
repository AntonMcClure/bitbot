#--depends-on commands

import json, re
from src import ModuleManager, utils

URL_URBANDICTIONARY = "http://api.urbandictionary.com/v0/define"
REGEX_DEFNUMBER = re.compile("-n ?(\d+) ")

class Module(ModuleManager.BaseModule):
    _name = "UrbanDictionary"

    @utils.hook("received.command.ud", alias_of="urbandictionary")
    @utils.hook("received.command.urbandictionary", min_args=1)
    def ud(self, event):
        """
        :help: Get the definition of a provided term from Urban Dictionary
        :usage: <term>
        """
        term = event["args"]
        number = 1
        match = re.match(REGEX_DEFNUMBER, term)
        if match:
            number = int(match.group(1))
            term = term.split(" ", 1)[1]
        page = utils.http.request(URL_URBANDICTIONARY,
            get_params={"term": term}, json=True)
        if page:
            if len(page.data["list"]):
                if number > 0 and len(page.data["list"]) > number-1:
                    definition = page.data["list"][number-1]
                    event["stdout"].write("%s: %s" % (definition["word"],
                        definition["definition"].replace("\n", " ").replace(
                        "\r", "").replace("  ", " ")))
                else:
                    event["stderr"].write("Definition number does not exist")
            else:
                event["stderr"].write("No results found")
        else:
            raise utils.EventsResultsError()
