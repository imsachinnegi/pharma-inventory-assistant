import nest_asyncio
nest_asyncio.apply()

import re

from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import (
    BasicMCPClient,
    McpToolSpec
)

# Ollama model
llm = Ollama(
    model="qwen2.5-coder:latest",
    request_timeout=120.0
)


class MCPAgent:

    def __init__(self):
        self.client = None
        self.tools = {}

    async def initialize(self):

        self.client = BasicMCPClient(
            "http://127.0.0.1:8000/sse"
        )

        mcp_tool = McpToolSpec(
            client=self.client
        )

        tool_list = await (
            mcp_tool.to_tool_list_async()
        )

        for tool in tool_list:
            self.tools[
                tool.metadata.name
            ] = tool

        print("Loaded Tools:")
        print(
            self.tools.keys()
        )

    async def run_tool(
        self,
        tool_name,
        **kwargs
    ):

        tool = self.tools.get(
            tool_name
        )

        if not tool:
            return (
                f"Tool not found: "
                f"{tool_name}"
            )

        result = await tool.acall(
            **kwargs
        )

        # Clean MCP response
        if hasattr(result, "content"):

            cleaned = []

            for item in result.content:

                if hasattr(
                    item,
                    "text"
                ):
                    cleaned.append(
                        item.text
                    )

            return "\n".join(
                cleaned
            )

        return str(result)

    async def chat(
        self,
        message
    ):

        text = (
            message.lower()
            .strip()
        )

        # Greeting - DO NOT use LLM
        if text in [
            "hi",
            "hello",
            "hey"
        ]:
            return (
                "Hello! I am your "
                "Pharma Inventory Assistant. "
                "Try commands like 'show inventory', "
                "'low stock', 'add medicine', etc."
            )

        # Add medicine - CHECK THIS FIRST (before expiry check!)
        if text.startswith("add") and "medicine" in text:

            prompt = f"""
Extract medicine info from user input.

User input:
{message}

Return ONLY this exact format (no extra text):

medicine_name: [name]
category: [category]
quantity: [number]
price: [number]
expiry_date: [YYYY-MM-DD]
supplier: [supplier name]

If any field is missing, use "Unknown" for text fields and 0 for numbers.
"""

            response = llm.complete(prompt)
            extracted = str(response)

            print("EXTRACTED:", extracted)

            try:
                medicine_name = re.search(
                    r"medicine_name:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                category = re.search(
                    r"category:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                quantity = int(
                    re.search(
                        r"quantity:\s*(\d+)",
                        extracted,
                        re.I
                    ).group(1)
                )

                price = float(
                    re.search(
                        r"price:\s*([\d.]+)",
                        extracted,
                        re.I
                    ).group(1)
                )

                expiry_date = re.search(
                    r"expiry_date:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                supplier = re.search(
                    r"supplier:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                print(f"DEBUG: Adding medicine: {medicine_name}")
                result = await self.run_tool(
                    "add_medicine",
                    medicine_name=medicine_name,
                    category=category,
                    quantity=quantity,
                    price=price,
                    expiry_date=expiry_date,
                    supplier=supplier
                )

                return f"✅ {result}: {medicine_name}"

            except Exception as e:
                print("ERROR:", e)
                return (
                    "❌ Could not parse medicine details. "
                    "Format: 'add medicine [name], category [cat], "
                    "quantity [num], price [num], "
                    "expiry_date [YYYY-MM-DD], supplier [name]'"
                )

        # Show inventory - FORCE tool call
        if (
            "show inventory" in text
            or "show medicines" in text
            or text == "inventory"
            or "all medicines" in text
            or "list medicines" in text
        ):
            print("DEBUG: Calling show_inventory tool")
            result = await self.run_tool("show_inventory")
            
            # Format the output nicely
            if result and result != "[]":
                return f"📋 Current Inventory:\n{result}"
            else:
                return "📋 Inventory is empty. Add medicines using 'add medicine' command."

        # Low stock - FORCE tool call
        if text == "low stock" or text == "low":
            print("DEBUG: Calling low_stock tool")
            result = await self.run_tool("low_stock")
            
            if result and result != "[]":
                return f"⚠️ Low Stock Medicines:\n{result}"
            else:
                return "✅ No medicines with low stock."

        # Expiry - FORCE tool call (only for exact commands, not when it's part of add medicine)
        if (
            text == "expiring soon"
            or text == "expiry"
            or text == "check expiry"
        ):
            print("DEBUG: Calling expiring_soon tool")
            result = await self.run_tool("expiring_soon")
            
            if result and result != "[]":
                return f"⏰ Medicines Expiring Soon:\n{result}"
            else:
                return "✅ No medicines expiring in the next 30 days."

        # Search medicine - FORCE tool call
        if "search" in text:
            medicine = (
                text.replace("search", "").strip()
            )
            
            if not medicine:
                return "Please specify medicine name. Example: 'search paracetamol'"
            
            print(f"DEBUG: Searching for: {medicine}")
            result = await self.run_tool(
                "search_medicine",
                medicine_name=medicine
            )
            
            if result and result != "[]":
                return f"🔍 Search Results for '{medicine}':\n{result}"
            else:
                return f"❌ No medicine found matching '{medicine}'"

        # Delete medicine - FORCE tool call
        if "delete" in text:
            medicine = (
                text.replace("delete", "").strip()
            )
            
            if not medicine:
                return "Please specify medicine name. Example: 'delete paracetamol'"
            
            print(f"DEBUG: Deleting: {medicine}")
            result = await self.run_tool(
                "delete_medicine",
                medicine_name=medicine
            )
            
            return f"✅ {result}"

        # Reduce stock - FORCE tool call
        if "sell" in text or "reduce" in text:
            match = re.search(
                r"(\d+)\s+([a-zA-Z0-9\s]+)",
                text
            )

            if match:
                amount = int(match.group(1))
                medicine = match.group(2).strip()
                
                print(f"DEBUG: Reducing {amount} of {medicine}")
                result = await self.run_tool(
                    "reduce_stock",
                    medicine_name=medicine,
                    amount=amount
                )
                
                return f"✅ Sold {amount} units of {medicine}. {result}"
            else:
                return "Format: 'sell [quantity] [medicine name]'. Example: 'sell 5 paracetamol'"

        # Add medicine - FORCE tool call
        if "add" in text and "medicine" in text:

            prompt = f"""
Extract medicine info from user input.

User input:
{message}

Return ONLY this exact format (no extra text):

medicine_name: [name]
category: [category]
quantity: [number]
price: [number]
expiry_date: [YYYY-MM-DD]
supplier: [supplier name]

If any field is missing, use "Unknown" for text fields and 0 for numbers.
"""

            response = llm.complete(prompt)
            extracted = str(response)

            print("EXTRACTED:", extracted)

            try:
                medicine_name = re.search(
                    r"medicine_name:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                category = re.search(
                    r"category:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                quantity = int(
                    re.search(
                        r"quantity:\s*(\d+)",
                        extracted,
                        re.I
                    ).group(1)
                )

                price = float(
                    re.search(
                        r"price:\s*([\d.]+)",
                        extracted,
                        re.I
                    ).group(1)
                )

                expiry_date = re.search(
                    r"expiry_date:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                supplier = re.search(
                    r"supplier:\s*(.*)",
                    extracted,
                    re.I
                ).group(1).strip()

                print(f"DEBUG: Adding medicine: {medicine_name}")
                result = await self.run_tool(
                    "add_medicine",
                    medicine_name=medicine_name,
                    category=category,
                    quantity=quantity,
                    price=price,
                    expiry_date=expiry_date,
                    supplier=supplier
                )

                return f"✅ {result}: {medicine_name}"

            except Exception as e:
                print("ERROR:", e)
                return (
                    "❌ Could not parse medicine details. "
                    "Format: 'add medicine [name], category [cat], "
                    "quantity [num], price [num], "
                    "expiry_date [YYYY-MM-DD], supplier [name]'"
                )

        # Help command
        if "help" in text or "commands" in text:
            return """
📋 Available Commands:
• show inventory - View all medicines
• low stock - Show medicines with quantity < 10
• expiring soon - Show medicines expiring in 30 days
• search [name] - Search for a medicine
• add medicine [details] - Add new medicine
• sell [qty] [name] - Reduce stock
• delete [name] - Delete a medicine

Example: "add medicine Paracetamol, category Painkiller, quantity 100, price 50, expiry_date 2026-12-31, supplier ABC"
"""

        # If nothing matches, use LLM for general chat
        # But make it clear we're a specialized assistant
        response = llm.complete(
            f"You are a Pharma Inventory Assistant. "
            f"The user said: '{message}'. "
            f"Respond briefly and suggest they use commands like "
            f"'show inventory', 'add medicine', 'search', etc."
        )

        return str(response)


mcp_agent = MCPAgent()