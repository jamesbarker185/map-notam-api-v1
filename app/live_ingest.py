import os
import time
import sys
import certifi
from dotenv import load_dotenv
from solace.messaging.messaging_service import MessagingService, ReconnectionListener, RetryStrategy
from solace.messaging.resources.queue import Queue
from solace.messaging.receiver.message_receiver import MessageHandler, InboundMessage
from .db_manager import DBManager
from .xml_parser import parse_notam_str

load_dotenv()

class ServiceEventHandler(ReconnectionListener):
    def on_reconnecting(self, e: Exception, event):
        print(f"Reconnecting: {e}")

    def on_reconnected(self, event):
        print(f"Reconnected event: {event}")

    def on_service_interruption(self, e: Exception, event):
        print(f"Service interrupted: {e}")

class IngestionHandler(MessageHandler):
    def __init__(self, db_manager):
        self.db = db_manager
        self.message_count = 0

    def on_message(self, message: InboundMessage):
        self.message_count += 1
        
        payload = message.get_payload_as_string() if message.get_payload_as_string() else str(message.get_payload_as_bytes())
        
        # Parse and Insert
        # Note: parse_notam_str handles exceptions internally and returns generator
        count = 0
        try:
            for notam in parse_notam_str(payload):
                self.db.insert_notam(notam)
                count += 1
                # Less verbose logging for prod, but good for now
                if count % 10 == 0:
                   sys.stdout.write(f"\r[INGEST] Processed {self.message_count} msgs. Last NOTAM: {notam.get('number', 'N/A')}")
                   sys.stdout.flush()
        except Exception as e:
            print(f"\n[ERROR] Processing message {self.message_count}: {e}")

def main():
    # Broker Configuration
    broker_props = {
        "solace.messaging.transport.host": os.getenv("SWIM_HOST"),
        "solace.messaging.service.vpn-name": os.getenv("SWIM_VPN"),
        "solace.messaging.authentication.scheme.basic.username": os.getenv("SWIM_USERNAME"),
        "solace.messaging.authentication.scheme.basic.password": os.getenv("SWIM_PASSWORD"),
        "solace.messaging.tls.trust-store-path": certifi.where(),
        "solace.messaging.tls.cert-validated": False
    }
    
    queue_name = os.getenv("SWIM_QUEUE")
    
    # Init DB
    print("Initializing Database...")
    db = DBManager()
    db.init_db()
    
    print("Initializing Messaging Service...")
    messaging_service = MessagingService.builder().from_properties(broker_props).build()
    messaging_service.connect()
    print("Connected to Solace Broker.")

    durable_exclusive_queue = Queue.durable_exclusive_queue(queue_name)
    receiver = messaging_service.create_persistent_message_receiver_builder().build(durable_exclusive_queue)
    receiver.start()
    
    msg_handler = IngestionHandler(db)
    print(f"Listening on queue: {queue_name} for real-time ingestion...")
    
    receiver.receive_async(msg_handler)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Terminating...")
        receiver.terminate()
        messaging_service.disconnect()

if __name__ == "__main__":
    main()
