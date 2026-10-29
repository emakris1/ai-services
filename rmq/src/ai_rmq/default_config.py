from pika import ConnectionParameters
from pika.credentials import PlainCredentials

DefaultHost = 'localhost'
DefaultPort = 5672
DefaultUsername = 'ai'
DefaultPassword = '1q2w3e4r!Q@W#E$R'

DefaultConnectionParameters = ConnectionParameters(
    host=DefaultHost,
    port=DefaultPort,
    credentials=PlainCredentials(username=DefaultUsername, password=DefaultPassword)
)
