from flask import Flask
from flask import json
from flask.globals import request
from flask.json import jsonify

app = Flask(__name__)

class Printer:

    def __init__(self, id, temp):
        self.id = id
        self.temp = temp
        self.state = False

printer_id_list = [1, 2, 4, 5, 6, 7, 8, 14]
printer_list = []
for id in printer_id_list:
    printer_list.append(Printer(id, 100))

print(vars(printer_list[0]))


@app.route('/printers/all/', methods=["GET", "POST"])
def api_all():
    out = []
    for printer in printer_list:
        out.append(vars(printer))
    return json.dumps(out)

@app.route('/printers/<int:id>/', methods=["GET", "POST"])
def api_id(id):
    for printer in printer_list:
        if printer.id == id:
            return json.dumps(vars(printer))
    return "No such ID found"

@app.route('/printers/<int:id>/resetbuildplate/', methods=["GET", "POST"])
def api_id_reset(id):
    if "reset" in request.args:
        resetstring = request.args["reset"]
    else:
        return "Error: specify 'reset' = true to clear build plate"
    print(resetstring)
    if resetstring.lower() == "true":
        for printer in printer_list:
            if printer.id == id:
                printer.state = True
                print("Printer ", printer.id, "command", id)
                return "True"
        # All checked, not found:
        return "Error: ID not found"
    elif resetstring.lower() == "false":
        for printer in printer_list:
                if printer.id == id:
                    printer.state = False
                    return "False"
        # All checked, not found:
        return "Error: ID not found"
    else:
        return "Error: wrong value - needs to be 'true' or 'false'"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=105)