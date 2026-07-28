import asyncio
import httpx

async def run_test():
    async with httpx.AsyncClient(base_url="http://localhost:8001/api/v1") as client:
        # Register a test user
        register_payload = {
            "name": "Test User",
            "email": "testchat@test.com",
            "password": "password123"
        }
        res = await client.post("/auth/register", json=register_payload)
        if res.status_code != 201:
            if res.status_code == 401 or res.status_code == 400: # try login if already exists
                res = await client.post("/auth/login", json={"email": "testchat@test.com", "password": "password123"})
        
        token = res.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create conversation
        res = await client.post("/chat/conversations", json={"title": "New Chat"}, headers=headers)
        conv_id = res.json()["id"]
        print(f"Created conversation: {conv_id}")
        
        # Send a message
        print("Sending message...")
        res = await client.post(
            f"/chat/conversations/{conv_id}/messages", 
            json={"content": "I earn 50000 rupees a month. How much should I save?"},
            headers=headers,
            timeout=15.0
        )
        print("Response status:", res.status_code)
        
        msgs = res.json()
        print("\nConversation history:")
        for m in msgs:
            print(f"[{m['role'].upper()}] {m['content']}")

if __name__ == "__main__":
    asyncio.run(run_test())
