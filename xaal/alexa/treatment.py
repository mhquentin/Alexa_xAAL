from security_check import authentication
from xaal.monitor import monitor
from xaal.lib import tools

import logging
import ast


PACKAGE_NAME = "xaal.alexa"
logger = logging.getLogger(PACKAGE_NAME)

global mMonitor
cfg = tools.load_cfg(PACKAGE_NAME)

def treatment(monitor, json_file):
    """ Receive the JSON and depending on the intent name send the intent content to the appropriate function """

    if (authentication(json_file)):
        logger.info("JSON from Amazon received : Successfully authenticated.")
        global mMonitor
        mMonitor = monitor
        
        if ("intent" in json_file["request"]):
            intent = json_file["request"]["intent"]
            intent_name = intent["name"]
        
            dict_intentToFunc = {'Pepper':treatment_pepper,'GetHelp':treatment_help,'ManageScenario':treatment_scenario,'ManageLights':treatment_lights,'GetTemperature':treatment_thermo,'GetCO':treatment_CO2,'ManageShutter':treatment_shutter,'Manageequipment':treatment_equipment}
            func = dict_intentToFunc[intent_name]
            if (func != None):
                return json_builder(func(intent))
            else:
                return json_builder(cfg['config']['alexa_intent_impossible'])
    else:        
        return json_builder(cfg['config']['alexa_auth_impossible'])


def treatment_help(intent):
    """ Give some help and use case to the user """
    logger.info("User asking for Help")
    try:
        skill_help_value = get_slot_value(intent, "help")
        return cfg['config'][ast.literal_eval(cfg['config']['dict_keys_skillToXaal'])[skill_help_value]]
    except:
        return cfg['config']['alexa_help_impossible']


def treatment_lights(intent):
    """ Lights treatments : which lights has to be turn on / off """
    
    on_off_value = get_slot_value(intent, "on_off")
                
    if (on_off_value == "eteindre"):
        action = "turn_off"
        
    elif(on_off_value == "allumer"):
        action = "turn_on"
    
    lamps = []
    
    if("resolutions" in intent["slots"]["location"]):
       
        skill_location = str(get_slot_value(intent, "location"))
        xaal_location =  ast.literal_eval(cfg['config']['dict_location_skillToXaal'])[skill_location]

        lamps = get_device('lamp.basic', 'alexa_location', xaal_location)
        
        logger.info("User asking for action on the '" + xaal_location + "' lights.")
        
    
    elif ("resolutions" in intent["slots"]["group"]):
        xaal_group = ast.literal_eval(cfg['config']['dict_group_skillToXaal'])[str(get_slot_value(intent, "group"))]
        lamps = get_device('lamp.basic', 'alexa_group', str(xaal_group))
        
        logger.info("User asking for action on the  group" + xaal_group + " lights.")

    else:
        lamps = get_device('lamp.basic', None, None)
        logger.info("user asking for action on all lights")

    send_action(lamps, action)

    return cfg['config']['alexa_response']

def treatment_thermo(intent):
    """ Return the thermometer temperature if both thermometer AND temperature were found. Otherwise, return it is impossible to answer """
    
    if("resolutions" in intent["slots"]["location"]):
        skill_location = str(get_slot_value(intent, "location"))
        xaal_location =  ast.literal_eval(cfg['config']['dict_location_skillToXaal'])[skill_location]

        logger.info("User asking for the '" + xaal_location + "' temperature")

        try:
            thermometer = get_device("thermometer.basic", "alexa_location", xaal_location)
            temperature = thermometer[0].attributes["temperature"]
        except:
            if (xaal_location == "extérieur"):
                try:
                    thermometer = get_device("thermometer.basic", "alexa_location", "internet")
                    temperature = thermometer[0].attributes["temperature"]
                except:
                    temperature = None
            else:
                temperature = None

        if (temperature == None):
            result = cfg['config']['alexa_temp_impossible']
        else:
            result = (cfg['config']['alexa_temp_result']).replace("$value",str(temperature).replace(".",",").replace(",0",""))

    return result 

def treatment_CO2(intent):
    """ Return the C02 value if both co2 device AND attribute were found. Otherwise, return it is impossible to answer """
    
    result = None

    if("resolutions" in intent["slots"]["location"]):
        skill_location = str(get_slot_value(intent, "location"))
        xaal_location =  ast.literal_eval(cfg['config']['dict_location_skillToXaal'])[skill_location]

        logger.info("User asking for the '" + xaal_location + "' CO2")

        sensors = get_device("co2meter.basic", 'alexa_location', xaal_location)
        try:
            co2 = str(sensors[0].attributes['co2'])
            result = (cfg['config']['alexa_co2_result']).replace("$value", co2)
        except:
            result = (cfg['config']['alexa_co2_impossible']).replace("$location", skill_location)

    return result


def treatment_shutter(intent):
    """ Down or Up the all the shutters. If precised, act only on the shutters of a location """

    action = get_slot_value(intent, "command_shutter")
    if("resolutions" in intent["slots"]["location_shutter"]):
        skill_location = str(get_slot_value(intent, "location_shutter"))
        xaal_location =  ast.literal_eval(cfg['config']['dict_location_shutter_skillToXaal'])[skill_location] 
        shutters = get_device("shutter.position", 'alexa_location', xaal_location)

        logger.info("User asking for"+action+" on the '" + xaal_location  + "' shutters")  

    else:
        shutters = get_device("shutter.position", None, None)
        logger.info("User asking for "+action+" on all shutters")

    send_action(shutters, action)

    return None

def treatment_equipment(intent):
    """ Lights treatments : which lights has to be turn on / off """
    
    on_off_value = get_slot_value(intent, "on_off")
                
    if (on_off_value == "eteindre"):
        action = "turn_off"
        
    elif(on_off_value == "allumer"):
        action = "turn_on"
    
    equipments = []
    equipments_location = []

    if("resolutions" in intent["slots"]["equipment"]):
        skill_equipment = str(get_slot_value(intent, "equipment"))
        xaal_equipment =  ast.literal_eval(cfg['config']['dict_equipment_skillToXaal'])[skill_equipment]
        print(xaal_equipment)
        equipments = get_device('powerrelay.basic', 'alexa_equipment', xaal_equipment)
    
    if("resolutions" in intent["slots"]["location"]):
        skill_location = str(get_slot_value(intent, "location"))
        xaal_location =  ast.literal_eval(cfg['config']['dict_location_skillToXaal'])[skill_location]
        equipments_location = get_device('powerrelay.basic', 'alexa_location', xaal_location)
        logger.info("User asking for action on the '" + xaal_location + "' radio.")
        for device in equipments :
            if device not in equipments_location :
                while device in equipments :
                    del equipments[equipments.index(device)]
        
    else:
        equimpents = get_device('powerrelay.basic', None, None)
        logger.info("user asking for action on all powerrelay")
    send_action(equipments, action)
    return cfg['config']['alexa_response']

def treatment_scenario(intent):
    result = None
    
    action_value = get_slot_value(intent, "scenario_action")
          
    if (action_value == "activer"):
        action = "on"
        
    elif(action_value == "desactiver"):
        action = "off"
    
    if("resolutions" in intent["slots"]["scenario"]):
       
        skill_scenario = str(get_slot_value(intent, "scenario"))
        xaal_scenario =  ast.literal_eval(cfg['config']['dict_scenario_skillToXaal'])[skill_scenario]
        print('xaal_scenario: ',xaal_scenario)
        if("resolutions" in intent["slots"]["group"]):
            xaal_group = ast.literal_eval(cfg['config']['dict_group_skillToXaal'])[str(get_slot_value(intent, "group"))]
            scenario = get_device('scenario.basic', 'alexa_scenario', str(xaal_group))

        else :
            scenario = get_device('scenario.basic', 'alexa_scenario', xaal_scenario)
        
        logger.info("User asking for action on the '" + xaal_scenario + "' scenario")
        send_action(scenario, action)
    return result

def treatment_pepper(intent):
    return cfg['config']['alexa_pepper_response']

def get_device(devType, metadataKey, metadataValue):
    """ Return the device of a Type. It is also possible to filter these devices with meta data"""
    result = []
    if ((metadataKey != None) and (metadataValue != None)):
        for device in mMonitor.devices.get_with_dev_type(devType):
            print(device)
            print(device.db.get(metadataKey))
            print(metadataKey)
            if (device.db.get(metadataKey) == metadataValue):
                result.append(device)
        if (len(result) == 0):
            raise Exception("Aucun équipement trouvé")
    else:
        result = mMonitor.devices.get_with_dev_type(devType)
    return result

def get_slot_value(intent, slot):
    """ Return the value of a slot """
    return intent["slots"][slot]["resolutions"]["resolutionsPerAuthority"][0]["values"][0]["value"]["name"]

def send_action(devices, action):
    """ Send action to a list of devices """

    for dev in devices:
        body = {}
        if dev:
            mMonitor.engine.send_request(mMonitor.dev,[dev.address,],action,body)
            
def json_builder(text):
    """ Return a dict ready to be parsed for JSON """
    
    if (text == None):
        res = {'version':'1.0',
                'response':{}}
    else:
        res = {'version':'1.0',
                'response':{
                    'outputSpeech':{
                        'type':'PlainText',
                        'text':text
                        }
                    }
                }
    return res
