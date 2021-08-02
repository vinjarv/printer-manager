import octorest
import time

class Printer:
    id, hostname, apikey, octopi_status = "", "", "", ""
    client = ()
    bed_temp, tool_temp = 0, 0
    available = False
    retryTimeout = 5 # Seconds between connection attempts when offline
    retryTimePrevious = 0 # Time at last connection attempt

    # Printer LCD animation
    __animation_state = 0
    __animation_lines = [
        "|",
        " "
    ]

    def __init__(self, id, api):
        self.hostname = "http://octopi" + id + ".local"
        self.apikey = api
        self.id = id
        self.__connect()
        self.update()
        

    def update(self):
        try:
            # get info from printer
            printerState = self.client.printer()

            self.bed_temp = printerState["temperature"]["bed"]["actual"]
            self.tool_temp = printerState["temperature"]["tool0"]["actual"]
            self.octopi_status = printerState["state"]["text"]
            # print("Status: " + self.octopi_status)
            # print("Hotend: " + str(self.tool_temp) + "C\n" + "Bed: " + str(self.bed_temp) + "C")

            # check if printer is unable to receive new job
            if printerState["state"]["flags"]["ready"] == False:
                self.available = False


            # Write message to printer LCD
            LCD_message = "Connected "
            if self.available:
                LCD_message = "Ready "

            LCD_message += self.__animation_lines[self.__animation_state]
            # Iterate over animation strings
            if self.__animation_state < len(self.__animation_lines) - 1:
                self.__animation_state += 1
            else:
                self.__animation_state = 0
            
            self.client.gcode("M117 " + LCD_message)

        except Exception as e:
            self.octopi_status = "Error"
            self.available = False
            print("Couldn't connect to " + self.hostname)
            print(e)

    def __connect(self):
        try:
            self.client = octorest.OctoRest(url=self.hostname, apikey=self.apikey)
            self.retryTimePrevious = time.time()
        except Exception as e:
            print("Couldn't begin connection to " + self.hostname)
            print(e)
            self.octopi_status = "Error"

    def autoConnect(self):
        currTime = time.time()
        if self.octopi_status == "Error" and currTime - self.retryTimeout >= self.retryTimePrevious:
            print("Autoconnecting: ....")
            self.__connect()
            self.update()
            self.retryTimePrevious = currTime
        
    def get_temp_string(self):
        return "Nozzle: " + str(self.tool_temp) + "℃ - " + "Bed: " + str(self.bed_temp) + "℃"