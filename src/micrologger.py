# This allows persistant logging as it writes logs to file. 
from file_updater import FileUpdater

class MicroLogger():
    self.file = "log.txt"
    self.shortened = "shortened_log.txt"
    self.MAX_LINES = 25 #max number of lines in file before deleting
    self.line_count = 0
    self.HOW_MANY_TO_TRIM = 10 # how many lines to trim off when replacing log file
    self.next_trimming = self.MAX_LINES

    def log(self, line):
        with open(self.file,'a') as f:
            self.line_count += 1
            f.write(str(self.line_count) + line)
        if self.line_count > self.next_trimming:
            self.keep_log_trimmed()
    
    def keep_log_trimmed(self) -> bool:
        self.next_trimming += self.HOW_MANY_TO_TRIM
        try:
            self._make_new_shortened_log()
            f = FileUpdater(old_file=self.file,new_file=self.shortened)
            f._copy_file(fromPath=self.shortened,toPath=self.file)
            return True
        except:
            self.log("Failed to copy file line 27 in MicroLogger()")
    
    def _make_new_shortened_log(self):
        with open(self.file,'r') as original:
            line_count = 0
            with open(self.shortened,'w') as shortened:
                for line in original:
                    line_count += 1
                    if line_count > self.HOW_MANY_TO_TRIM:
                        shortened.write(line)
    