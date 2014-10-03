# -*- encoding: utf-8 -*-
import web
import presenters

if __name__ == "__main__":
    app = web.application(presenters.urls, globals())
    app.run()
