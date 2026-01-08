import asyncio
from pyrogram import Client

async def generate_session():
    try:
        api_id_input = input("Enter API_ID: ").strip()
        if not api_id_input: return
        
        api_id = int(api_id_input)
        api_hash = input("Enter API_HASH: ").strip()
        if not api_hash: return
        
        app = Client(
            "my_session_gen",
            api_id=api_id,
            api_hash=api_hash,
            in_memory=True
        )
        
        async with app:
            session_string = await app.export_session_string()
            print(f"\n{session_string}")
            
    except (ValueError, Exception):
        pass

if __name__ == "__main__":
    try:
        asyncio.run(generate_session())
    except KeyboardInterrupt:
        pass