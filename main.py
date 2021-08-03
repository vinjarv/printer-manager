import time
import configparser
import threading

from printer import Printer
from GUI import Application
from filemonitor import Watcher
from api import ApiHandler


# Get printer id and API key from INI file
# Format: ID = API_KEY
#
# [PRINTERS]
# 01 = 1234567890ABCDEF
# 02 = 1234567890ABCDEF
#
config = configparser.ConfigParser()
config.read("./Config/config.ini")
printer_conf = config["PRINTERS"]


printer_connection_settings = []
for printer in printer_conf:
    printer_connection_settings.append([printer, printer_conf[printer]])


if __name__ == '__main__':

    printers = [Printer(id=connection_settings[0], api=connection_settings[1]) for connection_settings in printer_connection_settings]
    print("Printers online: ", end="")
    for printer in printers:
        print(printer.id + " ",end = "")
    print("")

    app = Application(printer_connection_settings, printers)

    watcher = Watcher(printers)

    api_handler = ApiHandler(printers)

    # Asynchronous printer update logic
    def printer_update_async(printer):
        update_delay = 1 # seconds
        while True:
            start_time = time.time()
            printer.autoConnect()
            if not printer.octopi_status == "Error":
                printer.update()
            # Wait for delay
            while not time.time() >= start_time + update_delay:
                time.sleep(0.1)

    # Create list of threads, one for each printer
    # Starts update function as background processes
    thread_list = []
    for index, printer in enumerate(printers):
            thread_list.append(threading.Thread(target=printer_update_async, args=(printer, ), daemon=True))
            thread_list[index].start()

    # Create thread for API handler
    api_thread = threading.Thread(target=api_handler.run, daemon=True)
    api_thread.start()

    while True:
        # replaces app.mainloop()
        app.update_idletasks()
        app.update()

        app.update_texts()

# TODO: Add flask server for API
        watcher.update()