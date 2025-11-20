from pika import ConnectionParameters
from pika.credentials import PlainCredentials

DefaultHost = 'localhost'
DefaultPort = 5672
DefaultUsername = 'guest'
DefaultPassword = 'guest'

DefaultConnectionParameters = ConnectionParameters(
    host=DefaultHost,
    port=DefaultPort,
    credentials=PlainCredentials(username=DefaultUsername, password=DefaultPassword)
)
