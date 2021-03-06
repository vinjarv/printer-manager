import tkinter as tk
from tkinter import ttk
from tkinter.constants import ACTIVE, DISABLED, NORMAL
from tkinter.messagebox import askyesno

class Application(tk.Frame):
    def __init__(self, printer_connection_settings, printers):
        self.printers = printers
        self.printer_connection_settings = printer_connection_settings
        self.root = tk.Tk()
        self.root.title("3D Printer Manager")
        img = tk.PhotoImage(file='icon.png')
        self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        self.content_frame = ttk.Frame(self.root, padding=(10, 10, 10, 10))
        self.content_frame.pack(side="top", padx=10, pady=10, fill="both")
        super().__init__(self.root)
        self.master = self.root
        self.create_widgets()

        # Set up resize of widgets on window size change, dynamic grid
        self.content_frame.columns = None
        self.root.bind("<Configure>", lambda resizecontent:self.resize_grid(self.content_frame))


    def create_widgets(self):
        self.printer_frames = []
        s = ttk.Style()
        s.configure("TLabelframe.Label", font=("Helvetica", 16))

        for i, line in enumerate(self.printer_connection_settings):
            self.printer_frames.append(ttk.LabelFrame(self.content_frame, text=str(line[0]), padding=(3, 3, 3, 3), ))
            self.printer_frames[i].grid(row=i//4, column=i%4)

            self.printer_frames[i].button = tk.Button(self.printer_frames[i], width=15, height=3)
            self.printer_frames[i].button["text"] = "Build plate status"
            self.printer_frames[i].button["command"] = lambda c=line[0]: self.handle_button_reset(c)
            self.printer_frames[i].button.pack(side="top")

            self.printer_frames[i].status_text = ttk.Label(self.printer_frames[i], text=self.printers[i].octopi_status)
            self.printer_frames[i].status_text.pack(side="top")

            self.printer_frames[i].temp_text = ttk.Label(self.printer_frames[i], text=self.printers[i].get_temp_string())
            self.printer_frames[i].temp_text.pack(side="top")


            self.printer_frames[i].job_text = tk.Text(self.printer_frames[i], width=15, height=1, wrap="none")
            self.printer_frames[i].job_text.pack(side="top")
            self.printer_frames[i].job_text_scroll = ttk.Scrollbar(self.printer_frames[i], orient="horizontal", 
                command=self.printer_frames[i].job_text.xview)
            self.printer_frames[i].job_text_scroll.pack(side="top", fill="x")

            self.printer_frames[i].progressbar = ttk.Progressbar(self.printer_frames[i], value=self.printers[i].job_progress)
            self.printer_frames[i].progressbar.pack(side="top", fill="x")

            self.printer_frames[i].eta_text = ttk.Label(self.printer_frames[i], text=self.format_time_remaining(self.printers[i].job_time_left))
            self.printer_frames[i].eta_text.pack(side="top")

        # self.quit = tk.Button(self, text="QUIT", fg="red",
        #                       command=self.master.destroy)
        # self.quit.pack(side="bottom")

    def resize_grid(self, frame):
        width = frame.winfo_width()
        slaves = frame.grid_slaves()
        slaves.reverse() # get widgets in correct, chronologic order
        max_width = max(slave.winfo_width() for slave in slaves)
        cols = width // max_width
        if cols == 0:
            cols = 1 # Avoid division by zero
        if cols == frame.columns: # Don't regrid if columns are unchanged
            return
        for i, slave in enumerate(slaves):
            slave.grid_forget()
            slave.grid(row=i//cols, column=i%cols)
        frame.columns = cols

    def handle_button_reset(self, id):
        # get related printer
        printer_index = 1e9 # set high to ensure error if number is wrong somehow
        for index, line in enumerate(self.printer_connection_settings):
            if id == line[0]:
                printer_index = index
        
        if self.printers[printer_index].available:
            # Turn off if flag is already enabled
            self.printers[printer_index].available = False
        else:
            # Ask for confirmation to disable
            confirmation = askyesno(title='Reset confirmation printer '+ id ,
                                    message='Confirm that build plate is clear and clean on printer ' + id,
                                    default='no')
            if confirmation:
                print("Reset printer " + id)
                self.printers[printer_index].available = True

    def update_printers(self):
        for i, frame in enumerate(self.printer_frames):
            frame.status_text.config(text=self.printers[i].octopi_status)
            frame.temp_text.config(text=self.printers[i].get_temp_string())
        
            if self.printers[i].available:
                frame.button["bg"] = "green"
            elif self.printers[i].octopi_status == "Error":
                frame.button["bg"] = "grey"
            else:
                frame.button["bg"] = "red"
            
            # Update job status fields
            frame.job_text.config(state=NORMAL)
            frame.job_text.delete("1.0", "2.0")
            frame.job_text.insert("end", str(self.printers[i].job_name))
            frame.job_text.config(state=DISABLED)
            frame.progressbar.config(value=self.printers[i].job_progress)
            frame.eta_text.config(text=self.format_time_remaining(self.printers[i].job_time_left))

    def format_time_remaining(self, seconds):
        if seconds == None:
            seconds = 0
        seconds = int(seconds)
        d = int(seconds/(60*60*24)) 
        h = int(seconds/(60*60) % 24) # up to 24
        m = int(seconds/60 % 60) # up to 60
        out = "ETA: "
        if d > 0:
            out += str(d).zfill(2) + "D"
        out += str(h).zfill(2) + "H"
        out += str(m).zfill(2) + "M"
        return out