import socket
import sys
import socketserver


class ClickControlSocket():

    BANNER_MAIN = "Click::ControlSocket"
    SOCKET_PATH = "/var/run/click"
    BUFFER_SIZE = 4096

    def __init__(self, path=SOCKET_PATH):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.path = path
        self.__connect()

    def __connect(self):
        try:
            self.sock.connect(self.path)
            banner_raw = self.sock.recv(self.BUFFER_SIZE)
            banner = banner_raw.decode('utf-8')
            if not banner.split("/")[0] == self.BANNER_MAIN:
                raise Exception
        except:
            self.__error("failed to create socket connection")

    def __detach(self):
        try:
            self.sock.detach()
        except:
            pass

    def __error(self, message):
        self.__detach()
        print("error: " + message)
        sys.exit(1)

    def __exec(self, command):
#        try:
            self.sock.sendall(bytes(command + "\n", 'utf-8'))
            output_raw = self.sock.recv(4096)
            output = output_raw.decode('utf-8').split('\r\n', 3)
            status_parts = output[0].split(" ")
            status_code = status_parts[0]
            status_type = status_parts[1]
            if status_code != "200":
                self.__error("click control socket command failed: {}".format(output[0]))
            if status_type == "Read":
                # check the amount of data
                read_sz = int(output[1].split(" ")[1])
                remaining = read_sz - len(output[2])
                ret = output[2]
                while remaining > 0:
                    more = self.sock.recv(remaining)
                    remaining = remaining - len(more)
                    ret = ret + more.decode("utf-8")
                return ret
            else:
                return
#        except:
#            self.__error("click control socket command failed for unknown reason")

    def close(self, full=False):
        self.__detach()
        if full:
            try:
                self.sock.close()
            except:
                self.__error("could not close socket")

    def get_version(self):
        return self.__exec("READ version")

    def get_config(self):
        return self.__exec("READ config")

    def get_list(self):
        return self.__exec("READ list")

    def read_handler(self, element, handler):
        return self.__exec("READ {}.{}".format(element, handler))

    def write_handler(self, element, handler, data):
        self.__exec("WRITEDATA {}.{} {}\r\n{}\r\n".format(element, handler, len(bytes(data, 'utf-8')), data))

