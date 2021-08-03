import time
import os
import configparser
import threading

from printer import Printer
import GUI
from GUI import Application


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


class Watcher:
    INPUT_PATH = ".\\input_gcode\\"
    FINISHED_PATH = ".\\finished_gcode\\"

    def __init__(self):
        print("Watching " + self.INPUT_PATH)

    ## Format any string to ascii without whitespace
    # Octorest select function doesn't work unless this is done to the filenames
    def __formatToAscii(self, input_str):
        # remove whitespace
        out_str = input_str.replace(" ", "_")
        # change norwegian letters
        if out_str.isascii() == False:
            dic = {"æ":"ae", "Æ":"Ae", "ø":"o", "Ø":"O", "å":"aa", "Å":"Aa"}
            for i, j in dic.iteritems():
                out_str = out_str.replace(i, j)
            # remove other non-ascii letters
            out_str = out_str.encode("ascii", "ignore")
        return out_str

    # Returns a list of g-code files with valid filenames in the input directory
    def __getValidFiles(self):
        # Get list of all files and directories in monitored directory
        allFiles = os.listdir(self.INPUT_PATH)
        validFiles = []

        # Check all files for type, store all STL files in validFiles
        for file in allFiles:
            try:
                # Separate file name and extension
                [name, extension] = file.rsplit(".", 1)
                if extension.lower() == "gcode":
                    # Ensure that file name is ASCII without spaces
                    new_file_name = self.__formatToAscii(file)
                    if new_file_name != file:
                        # rename file, return new name
                        os.replace(self.INPUT_PATH + file, self.INPUT_PATH + new_file_name)
                        file = new_file_name
                        validFiles.append(new_file_name)
                    else:
                        # filename was valid, return original name
                        validFiles.append(file)
            except:
                print("Invalid file found: ", file)
        return validFiles

    # Main function in class
    # Gets files ready for print, gets available printers
    # Distributes print jobs
    def update(self):
        validFiles = self.__getValidFiles()
        # make a list of printers ready to recieve work
        available_printer_indexes = []
        for i, printer in enumerate(printers):
            if printer.available:
                available_printer_indexes.append(i)

        while len(available_printer_indexes) > 0 and len(validFiles) > 0:
                printer_index = available_printer_indexes.pop(0)
                file = validFiles.pop(0)
                print("File to print: " + file)
                try:
                    printers[printer_index].client.upload(self.INPUT_PATH + file)
                    printers[printer_index].client.select(file, print=True)
                    printers[printer_index].available = False
                    os.replace(self.INPUT_PATH + file, self.FINISHED_PATH + file)
                    print("Job " + file + " started on printer " + printers[printer_index].id)
                except Exception as e:
                    print("Couldn't start job")
                    print(e)


if __name__ == '__main__':

    printers = [Printer(id=connection_settings[0], api=connection_settings[1]) for connection_settings in printer_connection_settings]
    print("Printers online: ", end="")
    for printer in printers:
        print(printer.id + " ",end = "")
    print("")

    app = Application(printer_connection_settings, printers)

    watcher = Watcher()


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


    while True:
        # replaces app.mainloop()
        app.update_idletasks()
        app.update()

        app.update_texts()

# TODO: Add flask server for API
        watcher.update()