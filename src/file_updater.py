""" Starts access point to update files.
Primarily for the secrets.py file"""
import os


class FileUpdater():
    def __init__(self, directory="", old_file="secrets.py",new_file="new_secrets.py"):
        # constants:
        self.directory = directory
        self.old_file = old_file
        self.new_file = new_file
        self.old_val = old_val
        self.new_val = new_val
    
    def replace_str_in_file(self, old_val="", new_val="") -> bool:
        self._make_new_file(old_val, new_val)
        if self._new_file_exists():
            self._copy_file(self.directory + self.new_file, self.directory + self.old_file)
            self._rm_file()
            return True
        return False
    
    def _make_new_file(self, old_val, new_val):
        with open(self.directory + self.old_file, "r") as old_file:
            with open(self.directory + self.new_file, 'w') as new_file:
                for line in old_file:
                    new_file.write(line.replace(old_val, new_val))

    # Helper Functions:
    def _copy_file(self, fromPath, toPath):
        with open(fromPath) as fromFile:
            with open(toPath, 'w') as toFile:
                CHUNK_SIZE = 512 # bytes
                data = fromFile.read(CHUNK_SIZE)
                while data:
                    toFile.write(data)
                    data = fromFile.read(CHUNK_SIZE)

    def _rm_file(self):
        os.remove(self.new_file)

    def _new_file_exists(self, directory) -> bool:
        return self.new_file in os.listdir(directory)