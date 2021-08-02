import tkinter as tk
from tkinter import ttk
import time, os
from tkinter import font
from tkinter.messagebox import askyesno
import configparser
import threading

from printer import Printer


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


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.printer_frames = []
        s = ttk.Style()
        s.configure("TLabelframe.Label", font=("Helvetica", 16))

        for i, line in enumerate(printer_connection_settings):
            self.printer_frames.append(ttk.LabelFrame(content_frame, text=str(line[0]), padding=(3, 3, 3, 3)))
            self.printer_frames[i].pack(side="left", padx=10, pady=10)

            self.printer_frames[i].button = tk.Button(self.printer_frames[i])
            self.printer_frames[i].button["text"] = "Build plate status"
            self.printer_frames[i].button["command"] = lambda c=line[0]: self.handle_button_reset(c)
            self.printer_frames[i].button.pack(side="top")

            self.printer_frames[i].status_label = ttk.Label(self.printer_frames[i], text="Status:")
            self.printer_frames[i].status_label.pack(side="top")

            self.printer_frames[i].status_text = ttk.Label(self.printer_frames[i], text=printers[i].octopi_status)
            self.printer_frames[i].status_text.pack(side="top")

            self.printer_frames[i].temp_text = ttk.Label(self.printer_frames[i], text=printers[i].get_temp_string())
            self.printer_frames[i].temp_text.pack(side="top")

        # self.quit = tk.Button(self, text="QUIT", fg="red",
        #                       command=self.master.destroy)
        # self.quit.pack(side="bottom")

    def handle_button_reset(self, id):
        # get related printer
        printer_index = 1e9 # set high to ensure error if number is wrong somehow
        for index, line in enumerate(printer_connection_settings):
            if id == line[0]:
                printer_index = index
        
        if printers[printer_index].available:
            # Turn off if flag is already enabled
            printers[printer_index].available = False
        else:
            # Ask for confirmation to disable
            confirmation = askyesno(title='Reset confirmation printer '+ id ,
                                    message='Confirm that build plate is clear and clean on printer ' + id,
                                    default='no')
            if confirmation:
                print("Reset printer " + id)
                printers[printer_index].available = True


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

    root = tk.Tk()
    root.title("3D Printer Manager")
    img = tk.PhotoImage(file='icon.png')
    root.tk.call('wm', 'iconphoto', root._w, img)
    content_frame = ttk.Frame(root, padding=(10, 10, 10, 10))
    content_frame.pack(side="top", padx=10, pady=10)
    app = Application(master=root)

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
        
            ## Set button color
            # if printer.available:
            #     app.buttons[index]["bg"] = 'green'
            # elif printer.octopi_status == "Error":
            #     app.buttons[index]["bg"] = 'grey'
            # else:
            #     app.buttons[index]["bg"] = 'red'

        # Update texts
        for i, frame in enumerate(app.printer_frames):
            frame.status_text.config(text=printers[i].octopi_status)
            frame.temp_text.config(text=printers[i].get_temp_string())
        
            if printers[i].available:
                frame.button["bg"] = "green"
            elif printers[i].octopi_status == "Error":
                frame.button["bg"] = "grey"
            else:
                frame.button["bg"] = "red"

        watcher.update()