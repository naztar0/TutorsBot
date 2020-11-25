from asyncio import sleep
import datetime
from database_connection import DatabaseConnection


async def check():
    deleteQuery = "DELETE FROM chats WHERE created<(%s) AND active=0"
    while True:
        exp_date = datetime.datetime.now() - datetime.timedelta(hours=6)
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(deleteQuery, [exp_date])
        await sleep(1800)
