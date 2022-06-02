from clickControlSocket import ClickControlSocket

class read:
    def __init__(self, fileName):
        self.ccs = ClickControlSocket(path=fileName)
        self.fileName = fileName
        # self.title = title

    def write(self, title):
        # ccs = ClickControlSocket(path=file)
        with open(title, 'w') as f:
            f.write("Output: " + self.ccs.read_handler("rewriter", "tcp_table"))
            f.close()

    def read(self):
        # ccs = ClickControlSocket(path=file)
        print("Output: " + self.ccs.read_handler("rewriter", "tcp_table"))


# if __name__ == "__main__":
a = read("/var/run/click")
b = read("/var/run/click2")

a.write("1.txt")
# a.read()
print("------------------------------------")
b.write("2.txt")