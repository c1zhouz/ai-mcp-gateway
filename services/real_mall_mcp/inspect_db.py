import asyncio
import aiomysql

async def inspect():
    conn = await aiomysql.connect(
        host='localhost',
        port=13306,
        user='root',
        password='123456',
        db='group_buy_market'
    )
    cur = await conn.cursor()
    await cur.execute("SHOW TABLES")
    tables = await cur.fetchall()
    for table in tables:
        table_name = table[0]
        print(f"Table: {table_name}")
        await cur.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = await cur.fetchall()
        for col in columns:
            print(f"  {col[0]} ({col[1]})")
        print()
    await cur.close()
    conn.close()

asyncio.run(inspect())
