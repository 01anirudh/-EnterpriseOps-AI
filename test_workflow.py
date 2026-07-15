import httpx
import asyncio

async def test_workflow():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Login
        print("Logging in...")
        res = await client.post("/api/auth/login", data={
            "username": "admin@demo.com",
            "password": "admin123"
        })
        res.raise_for_status()
        token = res.json()["access_token"]
        print(f"Logged in successfully. Token: {token[:10]}...")

        client.headers.update({"Authorization": f"Bearer {token}"})

        # 2. Submit workflow
        print("Submitting workflow...")
        prompt = "Analyze Q2 sales, check our discount policy, generate an executive report, and email the finance team."
        res = await client.post("/api/workflow", json={"prompt": prompt})
        print(f"POST status: {res.status_code}")
        print(f"POST body: {res.text}")
        res.raise_for_status()
        data = res.json()
        task_id = data["task_id"]
        print(f"Workflow submitted! Task ID: {task_id}")

        # 3. Check status
        for _ in range(10):
            await asyncio.sleep(2)
            res = await client.get("/api/workflow")
            tasks = res.json()
            task = next((t for t in tasks if t["id"] == task_id), None)
            if task:
                print(f"Task status: {task['status']}")
                if task['status'] in ['completed', 'failed', 'awaiting_approval']:
                    break
            else:
                print("Task not found in list")

if __name__ == "__main__":
    asyncio.run(test_workflow())
