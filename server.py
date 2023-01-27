#  coding: utf-8 
import socketserver
import pathlib
import os

# Copyright 2023 Abram Hindle, Eddie Antonio Santos, Curtis Kennedy
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2023 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()

        self.debug = False
        if self.debug:
            print ("Got a request of: %s\n" % self.data)
        # self.request.sendall(bytearray("OK",'utf-8'))
        self.parse()

    def send_405(self):
        if self.debug:
            print("SENDING 405 Method Not Allowed")
        self.request.sendall(bytearray("HTTP/1.1 405 Method Not Allowed\r\ncontent-type: text/html; charset=utf-8\r\n", 'utf-8'))

    def send_400(self):
        if self.debug:
            print("SENDING 400 Bad Request")
        self.request.sendall(bytearray("HTTP/1.1 400 Bad Request\r\ncontent-type: text/html; charset=utf-8\r\n", 'utf-8'))

    def send_404(self):
        if self.debug:
            print("SENDING 404 Not Found")
        self.request.sendall(bytearray("HTTP/1.1 404 Not Found\r\ncontent-type: text/html; charset=utf-8\r\n", 'utf-8'))

    def send_301(self, new_dest : str):
        if self.debug:
            print("SENDING 301 Moved Permanently")
        self.request.sendall(bytearray(f"HTTP/1.1 301 Moved Permanently\r\ncontent-type: text/html; charset=utf-8\r\nLocation: {new_dest}\r\n", 'utf-8'))

    def send_200(self, type: str, content=bytearray()):
        if self.debug:
            print("SENDING 200 OK")
        ba = bytearray(f"HTTP/1.1 200 OK\r\ncontent-type: {type}; charset=utf-8\r\n\r\n", 'utf-8')
        res = ba + content
        self.request.sendall(res)

    def parse(self):
        encode = "utf-8"
        req = self.data.decode(encode)
        split_req = req.split()
        # check that this is not a POST, PUT, or DELETE request etc.
        if split_req[0] in ["PUT", "POST", "DELETE", "HEAD", "CONNECT", "OPTIONS", "TRACE", "PATCH"]:
            # 405
            self.send_405()
            return
        # check that this is a GET request --> and not some made up thing
        # if req[0:4] != "GET ":
        if split_req[0] != "GET":
            self.send_400()
            return
        # we have a get request!
        if self.debug:
            print(f"SPLIT_REQ = {split_req}")

        # next is path
        path = split_req[1]
        is_path_dir = True if path.endswith("/") else False
        # prevent going outside of www
        libpath_without_www = pathlib.Path(path).resolve()
        libpath_without_www_str = str(libpath_without_www)
        libpath = pathlib.Path("./www"+libpath_without_www_str)
        libpath_str = str(libpath)
        if self.debug:
            print("PATH =", libpath)

        # is this a directory? is this a file?
        isfile = False
        isdir = False
        if os.path.isdir(libpath_str):
            if self.debug:
                print("THIS IS A DIRECTORY")
            isdir = True
        if os.path.isfile(libpath_str):
            if self.debug:
                print("THIS IS A FILE")
            isfile = True

        # if this is a directory, did the path end with a /?
        if isdir and not is_path_dir:
            # print("301 CORRECT PATH")
            self.send_301("http://127.0.0.1:8080" + libpath_without_www_str + "/")
            return
        
        # if this is a directory, is there an index.html?
        if isdir:
            index_path = libpath_str + "/index.html"
            if self.debug:
                print(f"Does {index_path} exist?")
            if os.path.isfile(index_path):
                # yes
                if self.debug:
                    print("YES")
                with open(str(pathlib.Path(index_path)), "r", encoding="utf-8") as f:
                    content = f.read()
                    self.send_200(content=bytearray(content, "utf-8"), type="text/html")
                return
            else:
                # no
                if self.debug:
                    print("NO")
                self.send_404()
                return
        
        # if this is a file, serve it
        if isfile:
            # what type of file
            with open((libpath_str), "r", encoding="utf-8") as f:
                content = bytearray(f.read(), "utf-8")
            if libpath_str.endswith(".html"):
                self.send_200(content=content, type="text/html")
            elif libpath_str.endswith(".css"):
                self.send_200(content=content, type="text/css")
            else:
                self.send_200(content=content, type="application/octet-stream")
            return
        else:
            self.send_404()
            return


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
