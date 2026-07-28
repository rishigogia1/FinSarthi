import asyncio
import httpx
import time

async def run_test():
    async with httpx.AsyncClient(base_url="http://localhost:8001/api/v1") as client:
        # Register a test user
        register_payload = {
            "name": "Dash User",
            "email": "dashuser2@test.com",
            "password": "password123"
        }
        res = await client.post("/auth/register", json=register_payload)
        if res.status_code != 201:
            if res.status_code == 401 or res.status_code == 400: # try login if already exists
                res = await client.post("/auth/login", json={"email": "dashuser2@test.com", "password": "password123"})
        
        token = res.json()["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test dashboard API
        print("Fetching dashboard...")
        start_time = time.time()
        res = await client.get("/dashboard/team", headers=headers, timeout=5.0)
        end_time = time.time()
        
        print("Response status:", res.status_code)
        
        if res.status_code == 200:
            data = res.json()
            print(f"Server reported total_time_ms: {data['total_time_ms']} ms")
            print(f"Client measured time: {(end_time - start_time) * 1000:.2f} ms")
            
            for agent in data["agents"]:
                print(f"\n[{agent['name']}] Status: {agent['status']} | Progress: {agent['progress']}")
                print(f"Activities: {agent['activities']}")
        else:
            print(res.text)

if __name__ == "__main__":
    asyncio.run(run_test())
