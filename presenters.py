# -*- coding: utf-8 -*-
import web

class BasePresenter:
    def POST(self, *args, **kwargs):
        self.method = 'POST'
        return self.request(*args, **kwargs)

    def GET(self, *args, **kwargs):
        self.method = 'GET'
        return self.request(*args, **kwargs)

    def request(self):
        raise Exception("Define method request or GET and POST")

class Article(BasePresenter):
    def request(self, par = None):
        return "Punx not dead volové: " + ("nic" if par is None else str(par))

# URLs
urls = (
    '/', Article, 
    '/article/(.*)', Article
)
