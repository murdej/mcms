from core import Core
core = Core()
import models,  sys

if len(sys.argv) > 1:
    cmd = sys.argv[1]
    if cmd == "dbcreate":
        print "Creating DB in :",  core.dbe
        models.BaseModel.metadata.create_all(core.dbe) 
