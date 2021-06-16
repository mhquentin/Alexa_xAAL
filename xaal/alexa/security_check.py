import json
from xaal.lib import tools

PACKAGE_NAME = "xaal.alexa"

def authentication(json):
    cfg = tools.load_cfg(PACKAGE_NAME)
    app_id = cfg['config']['app_id']
    user_id = cfg['config']['user_id']
    if (json['context']['System']['application']['applicationId'] == app_id):
        if (json['context']['System']['user']['userId'] == user_id):
            return True
    return False
