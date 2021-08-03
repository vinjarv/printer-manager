from flask import Flask, json
from flask.globals import request

class ApiHandler:
    def __init__(self, printers):
        self.printers = printers
        self.app = Flask(__name__)
        self.init_handlers()

    def init_handlers(self):
        @self.app.route('/printers/', methods=["GET", "POST"])
        def get_all_printers():
            lines = []
            for printer in self.printers:
                lines.append(printer.get_vars_as_dict())
            return json.dumps(lines)

        @self.app.route('/printers/<int:id>/', methods=["GET", "POST"])
        def get_one_printer(id):
            for printer in self.printers:
                if id == int(printer.id):
                    return json.dumps(printer.get_vars_as_dict())
            return "Error: invalid ID"

        @self.app.route('/printers/<int:id>/clear/', methods=["GET", "POST"])
        def clear_plate(id):
            id_list = []
            for printer in self.printers:
                id_list.append(int(printer.id))

            if id in id_list:
                if "clear" in request.args:
                    reset_string = request.args["clear"]
                else:
                    return "Invalid query string. \n Usage: ID/clear?clear=true or ID/clear?clear=false"
            else:
                return "Error: invalid ID"

            printer_index = id_list.index(id)
            printer = self.printers[printer_index]
            if reset_string.lower() == "true":  
                printer.available = True
                return json.dumps(printer.get_vars_as_dict())
            elif reset_string.lower() == "false":
                printer.available = False
                return json.dumps(printer.get_vars_as_dict())
            else:
                return "Error: query string must be boolean"
                

    def run(self):
        self.app.run(host="0.0.0.0", port=105)



