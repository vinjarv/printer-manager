import os
from autoslicer.autoslice import AutoSlicer

class Watcher:
    def __init__(self, printers, config):

        self.printers = printers
        self.CONFIG = config

        self.INPUT_PATH = self.CONFIG["PATHS"]["input_folder"]
        self.FINISHED_PATH = self.CONFIG["PATHS"]["finished_folder"]
        self.ERROR_PATH = self.CONFIG["PATHS"]["error_folder"]

        if not os.path.exists(self.INPUT_PATH):
            print("No input folder found, creating " + self.INPUT_PATH)
            os.mkdir(self.INPUT_PATH)
        if not os.path.exists(self.FINISHED_PATH):
            print("No finished folder found, creating " + self.FINISHED_PATH)
            os.mkdir(self.FINISHED_PATH)
        if not os.path.exists(self.ERROR_PATH):
            print("No error folder found, creating " + self.ERROR_PATH)
            os.mkdir(self.ERROR_PATH)

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

    # Returns a list of files with valid filenames in the input directory
    def __getValidFiles(self):
        # Get list of all files and directories in monitored directory
        allFiles = os.listdir(self.INPUT_PATH)
        model_files = []
        gcode_files = []

        # Check all files for type, store all accepted files in model_files or gcode_files
        for file in allFiles:
            try:
                # Separate file name and extension
                [name, extension] = file.rsplit(".", 1)
                if extension.lower() in ["gcode", "stl", "3mf"]:
                    # Ensure that file name is ASCII without spaces
                    new_file_name = self.__formatToAscii(file)
                    if new_file_name != file:
                        # rename file, return new name
                        os.replace(self.INPUT_PATH + file, self.INPUT_PATH + new_file_name)
                        file = new_file_name
                    # Add to list
                    if extension.lower() == "gcode":
                        gcode_files.append(file)
                    else:
                        model_files.append(file)
            except:
                print("Invalid file found: ", file)
        # print("Models:", model_files)
        # print("GCODE:", gcode_files)
        return model_files, gcode_files

    # Run autoslicer on list of 3D files
    def __sliceFiles(self, model_files):
        autoslicer = AutoSlicer(self.CONFIG["PATHS"]["slicer_path"], self.CONFIG["PATHS"]["slicer_config_path"])
        for file in model_files:
            print(file)
            try:
                autoslicer.slice(os.path.join(self.INPUT_PATH, file), self.INPUT_PATH)
            except:
                print("File", file, "failed to slice")
                # Move to "error_files"
                os.replace(os.path.join(self.INPUT_PATH, file), os.path.join(self.ERROR_PATH, file))
            # Move to "finished_files"
            os.replace(os.path.join(self.INPUT_PATH, file), os.path.join(self.FINISHED_PATH, file))

    # Send GCODE files to printers
    def __sendFiles(self, gcode_files):
        # make a list of printers ready to recieve work
        available_printer_indexes = []
        for i, printer in enumerate(self.printers):
            if printer.available:
                available_printer_indexes.append(i)
        
        while len(available_printer_indexes) > 0 and len(gcode_files) > 0:
                printer_index = available_printer_indexes.pop(0)
                file = gcode_files.pop(0)
                print("File to print: " + file)
                try:
                    self.printers[printer_index].client.upload(self.INPUT_PATH + file)
                    self.printers[printer_index].client.select(file, print=True)
                    self.printers[printer_index].available = False
                    os.replace(self.INPUT_PATH + file, self.FINISHED_PATH + file)
                    print("Job " + file + " started on printer " + self.printers[printer_index].id)
                except Exception as e:
                    print("Couldn't start job")
                    print(e)

    # Main function in class
    # Gets files ready for print, gets available printers
    # Distributes print jobs
    def update(self):
        model_files, gcode_files = self.__getValidFiles()
        self.__sliceFiles(model_files)
        self.__sendFiles(gcode_files)