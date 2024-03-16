# -*- coding:utf-8 -*-
import requests
import json
import re
import os
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
# os.environ["http_proxy"] = "http://127.0.0.1:20172"
# os.environ["https_proxy"] = "http://127.0.0.1:20172"
from robot import logging
from robot import config
from robot.sdk.AbstractPlugin import AbstractPlugin
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_structured_chat_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import tool, Tool, initialize_agent, load_tools
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.pydantic_v1 import BaseModel, Field


logger = logging.getLogger(__name__)


hass_url = config.get('jarvis')['hass']['host']
hass_port = config.get('jarvis')['hass']['port']
hass_headers = {'Authorization': config.get('jarvis')['hass']['key'], 'content-type': 'application/json'}

class BrightnessControlInput(BaseModel):
    entity_id: str 
    brightness_pct: int
    
class FeederOutInput(BaseModel):
    entity_id: str
    nums: int

class HvacControlInput(BaseModel):
    entity_id: str
    input_dict: dict


class Plugin(AbstractPlugin):

    SLUG = "jarvis"
    DEVICES = None
    PRIORITY = config.get('jarvis')['priority']
    
    def __init__(self, con):
        super().__init__(con)
        self.profile = config.get()
        self.langchain_init()
        
    def langchain_init(self):
        self.llm = AzureChatOpenAI(azure_deployment="gpt-35-turbo")
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        structured_chat_prompt = hub.pull("hwchase17/structured-chat-agent")

        addtional_system_message = """You can control the devices and answer any other questions. In my House, the devices are as blow (in the dict, the value is use purpose, the key is the entity_id):
        {device_list}. You can control the devices by using the given tools. You must use the correct parameters when using the tools. Sometimes before you change the value of some device, 
        you should first query the current state of the device to confirm how to change the value. I'm in '{location}' now. ALWAYS outputs the final result to {language}."""
        structured_chat_system = structured_chat_prompt.messages[0].prompt.template
        structured_chat_human = structured_chat_prompt.messages[2].prompt.template
        prompt = ChatPromptTemplate.from_messages([
            ('system', structured_chat_system+ addtional_system_message),
            structured_chat_human
            ]
        )
        
        brightness_control_tool = StructuredTool(
            name="brightness_control",
            description="Control the brightness of a light. the brightness_pct must be between 10 and 100 when you just ajust the brightness, but if you want to turn off the light, brightness should be set to 0. input: brightness_pct: int, entity_id: str, output: bool.",
            func=self.brightness_control,
            args_schema=BrightnessControlInput
        )
        
        feeder_out_tool = StructuredTool(
            name="feeder_out",
            description="Control the pet feeder. You can Only use this tool when you need to feed. The nums must be between 1 and 10, input: nums: int, entity_id: str, output: bool.",
            func=self.feeder_out,
            args_schema=FeederOutInput
        )
        
        get_attr_tool = Tool(
            name="get_attributes",
            description="Get the attributes of a device. input: entity_id: str, output: dict.",
            func=self.get_attributes
        )
        
        hvac_control_tool = StructuredTool(
            name="hvac_control",
            description="""Control the hvac. input: entity_id: str, input_dict: dict, output: bool. input_dict include: operation (set_hvac_mode, set_fan_mode, set_temperature), 
            hvac_mode (off, auto, cool, heat, dry, fan_only), temperature, fan_mode ('Fan Speed Down', 'Fan Speed Up'), You must choose at least one operation and Pass the corresponding parameter (ONLY ONE) as needed.
            """,
            func=self.hvac_control,
            args_schema=HvacControlInput
        )
        
        internal_tools = load_tools(["openweathermap-api", "google-search"], self.llm)
        
        
        tools = [brightness_control_tool, feeder_out_tool, get_attr_tool, hvac_control_tool
                 ] + internal_tools
        agent = create_structured_chat_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3, handle_parsing_errors=True)
        self.device_dict = self.profile['jarvis']['entity_ids']

    def handle(self, text, parsed):
        handle_result = self.agent_executor.invoke({"input": f"{text}", "device_list": self.profile["jarvis"]['entity_ids'],
                                                    "location": self.profile['location'], 
                                                    "language": f"{self.profile['jarvis']['language']}"})
        output_text = handle_result["output"]
        self.say(output_text, cache=True)

    @staticmethod
    def brightness_control(entity_id, brightness_pct):
        data = {"entity_id": entity_id,
                "brightness_pct": brightness_pct
        }
        p = json.dumps(data)
        domain = entity_id.split(".")[0]
        s = "/api/services/" + domain + "/"
        url_s = hass_url + ":" + hass_port + s + "turn_on"
        request = requests.post(url_s, headers=hass_headers, data=p)
        if format(request.status_code) == "200" or \
            format(request.status_code) == "201": 
            return True
        else:
            logger.error(format(request))
            return False
        
    @staticmethod
    def hvac_control(entity_id, input_dict:dict):
        data = {"entity_id": entity_id
                }
        operation = input_dict['operation']
        if input_dict.get("hvac_mode"):
            data["hvac_mode"] = input_dict.get("hvac_mode")
        if input_dict.get("temperature"):
            data["temperature"] = input_dict.get("temperature")
        if input_dict.get("fan_mode"):
            data["fan_mode"] = input_dict.get("fan_mode")
        p = json.dumps(data)
        domain = entity_id.split(".")[0]
        s = "/api/services/" + domain + "/"
        url_s = hass_url + ":" + hass_port + s + operation
        logger.info(f"url_s: {url_s}, data: {p}")
        request = requests.post(url_s, headers=hass_headers, data=p)
        if format(request.status_code) == "200" or \
            format(request.status_code) == "201": 
            return True
        else:
            logger.error(format(request))
            return False

    @staticmethod
    def feeder_out(entity_id, nums):
        domain = entity_id.split(".")[0]
        s = "/api/services/" + domain + "/"
        url_s = hass_url + ":" + hass_port + s + "turn_on"
        data = {
            "entity_id": entity_id,
            "variables": {"nums": nums}
        }
        p = json.dumps(data)
        request = requests.post(url_s, headers=hass_headers, data=p)
        if format(request.status_code) == "200" or \
            format(request.status_code) == "201": 
            return True
        else:
            logger.error(format(request))
            return False

    @staticmethod
    def get_attributes(entity_id):
        url_entity = hass_url + ":" + hass_port + "/api/states/" + entity_id
        device_state = requests.get(url_entity, headers=hass_headers).json()
        attributes = device_state['attributes']
        return attributes

    def isValid(self, text, parsed):

        return True
 
if __name__ == "__main__":
    # ajust_brightness()
    # get_state()
    # ajust_color_temp()
    # pet_feeder()
    # refresh_devices()
    pass
    # profile = config.get()
    # print(profile)