import asyncio
import os
import random
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database.models import Base
from backend.database.postgres import create_tables

async def seed_sales_db():
    print("Connecting to DB...")
    # Make sure tables exist
    await create_tables()

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # We need raw SQL for the custom sales table, so we'll execute text directly
        from sqlalchemy import text

        print("Creating sales table if not exists...")
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                year INTEGER,
                quarter VARCHAR(4),
                region VARCHAR(100),
                product_category VARCHAR(100),
                revenue DECIMAL(15,2),
                units_sold INTEGER,
                profit DECIMAL(15,2),
                sales_rep VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Clear existing
        await session.execute(text("TRUNCATE TABLE sales RESTART IDENTITY"))

        print("Generating mock sales data...")
        regions = ["North", "South", "East", "West", "International"]
        categories = ["Enterprise Software", "Cloud Infrastructure", "Consulting", "Hardware", "Support Subscriptions"]
        years = [2023, 2024]
        quarters = ["Q1", "Q2", "Q3", "Q4"]
        
        data = []
        for year in years:
            for q in quarters:
                for region in regions:
                    for cat in categories:
                        # Base revenue ranges
                        if cat == "Enterprise Software":
                            rev = random.uniform(500_000, 2_500_000)
                            margin = 0.85
                        elif cat == "Cloud Infrastructure":
                            rev = random.uniform(1_000_000, 4_000_000)
                            margin = 0.60
                        else:
                            rev = random.uniform(100_000, 800_000)
                            margin = 0.40
                            
                        # Add some seasonality and growth
                        if q == "Q4": rev *= 1.4
                        if year == 2024: rev *= 1.2
                        
                        units = int(rev / random.uniform(100, 5000))
                        profit = rev * margin
                        
                        data.append({
                            "year": year,
                            "quarter": q,
                            "region": region,
                            "product_category": cat,
                            "revenue": round(rev, 2),
                            "units_sold": units,
                            "profit": round(profit, 2),
                            "sales_rep": f"Rep {random.randint(1, 20)}"
                        })

        print(f"Inserting {len(data)} rows...")
        for row in data:
            await session.execute(
                text("""
                    INSERT INTO sales (year, quarter, region, product_category, revenue, units_sold, profit, sales_rep)
                    VALUES (:year, :quarter, :region, :product_category, :revenue, :units_sold, :profit, :sales_rep)
                """), row
            )
        
        # Also create a default admin user
        from backend.api.auth import hash_password
        
        print("Creating default admin user (admin@demo.com)...")
        await session.execute(text("DELETE FROM users WHERE email = 'admin@demo.com'"))
        await session.execute(
            text("""
                INSERT INTO users (id, name, email, hashed_password, role, is_active)
                VALUES (gen_random_uuid(), 'System Admin', 'admin@demo.com', :pw, 'manager', true)
            """), {"pw": hash_password("admin123")}
        )

        await session.commit()
        print("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_sales_db())
