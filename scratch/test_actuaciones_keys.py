import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

import asyncio
from backend.service.rama import actuaciones_proceso

async def main():
    print("Fetching actuaciones for process 93451451...")
    res = await actuaciones_proceso(93451451)
    print(f"Type of response: {type(res)}")
    if isinstance(res, list) and len(res) > 0:
        first = res[0]
        print("\nKeys in first event:")
        for k, v in first.items():
            print(f"  {k}: {repr(v)}")
    else:
        print("Response is empty or not a list")

asyncio.run(main())
