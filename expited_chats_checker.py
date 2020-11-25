from asyncio import sleep
import datetime
from database_connection import DatabaseConnection


async def check():
    deleteQuery = "DELETE FROM chats WHERE created<(%s)"
    while True:
        exp_date = datetime.datetime.now() - datetime.timedelta(days=14)
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(deleteQuery, [exp_date])
        await sleep(70000)
