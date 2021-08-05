import os

class Watcher:

    # TODO: Get from config
    INPUT_PATH = os.path.join(".", "input_gcode", "")
    FINISHED_PATH = os.path.join(".", "finished_gcode", "")

    def __init__(self, printers):
        self.printers = printers
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
        for i, printer in enumerate(self.printers):
            if printer.available:
                available_printer_indexes.append(i)

        while len(available_printer_indexes) > 0 and len(validFiles) > 0:
                printer_index = available_printer_indexes.pop(0)
                file = validFiles.pop(0)
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