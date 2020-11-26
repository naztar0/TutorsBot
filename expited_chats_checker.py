from asyncio import sleep
import datetime
from database_connection import DatabaseConnection


async def check():
    deleteChatQuery = "DELETE FROM chats WHERE created<(%s)"
    deleteTempQuery = "DELETE FROM chats WHERE created<(%s) AND active=0"
    deleteTextQuery = "DELETE FROM text_messages WHERE time<(%s)"
    deleteMediaQuery = "DELETE FROM media_messages WHERE time<(%s)"
    while True:
        date = datetime.datetime.now()
        exp_date = date - datetime.timedelta(days=14)
        exp_temp_date = date - datetime.timedelta(hours=6)
        with DatabaseConnection() as db:
            conn, cursor = db
            cursor.execute(deleteChatQuery, [exp_date])
            cursor.execute(deleteTempQuery, [exp_temp_date])
            cursor.execute(deleteTextQuery, [exp_date])
            cursor.execute(deleteMediaQuery, [exp_date])
            conn.commit()
        await sleep(1800)
