from ..tools.system import system_info
from ..tools.memory_tools import remember_fact


class Executor:


    def __init__(self):

        self.tools = {

            "system_info": system_info,
            "remember_fact": remember_fact

        }


    def execute(self, tool_name, context=None):


        if tool_name not in self.tools:

            return {

                "success": False,

                "error": f"Unknown tool: {tool_name}"

            }


        try:

            result = self.tools[tool_name](context)

            return {

                "success": True,

                "tool": tool_name,

                "result": result

            }


        except Exception as e:

            return {

                "success": False,

                "error": str(e)

            }


    def list_tools(self):

        return list(self.tools.keys())