import os
import time
import sys
import certifi
from dotenv import load_dotenv
from solace.messaging.messaging_service import MessagingService, ReconnectionListener, RetryStrategy
from solace.messaging.resources.queue import Queue
from solace.messaging.receiver.message_receiver import MessageHandler, InboundMessage

load_dotenv()

# Constants
OUTPUT_FILE = "raw_notam_dump.xml"
TIMEOUT_SECONDS = 60  # Initial wait time
SILENCE_TIMEOUT = 5   # Stop if no new messages for X seconds

class ServiceEventHandler(ReconnectionListener):
    def on_reconnecting(self, e: Exception, event):
        print(f"Reconnecting: {e}")

    def on_reconnected(self, event):
        print(f"Reconnected event: {event}")

    def on_service_interruption(self, e: Exception, event):
        print(f"Service interrupted: {e}")

class MessageDumper(MessageHandler):
    def __init__(self):
        self.message_count = 0
        self.last_message_time = time.time()

    def on_message(self, message: InboundMessage):
        self.message_count += 1
        self.last_message_time = time.time()
        
        payload = message.get_payload_as_string() if message.get_payload_as_string() else str(message.get_payload_as_bytes())
        
        # Strip XML Declaration to allow concatenation
        if payload.strip().startswith("<?xml"):
            try:
                # Find end of declaration ?>
                idx = payload.find("?>")
                if idx != -1:
                    payload = payload[idx+2:]
            except Exception:
                pass # Fallback to original payload if something weird happens

        # Determine payload size/info
        size = len(payload)
        sys.stdout.write(f"\r[INFO] Messages Received: {self.message_count} (Last size: {size})")
        sys.stdout.flush()
        
        # Append to file
        try:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(payload + "\n")
        except Exception as e:
            print(f"\n[ERROR] Failed to write message: {e}")

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
    
    print("Initializing Messaging Service...")
    messaging_service = MessagingService.builder().from_properties(broker_props).build()
    messaging_service.connect()
    print("Connected to Solace Broker.")

    # Initialize Output File with Root Tag
    print(f"Preparing {OUTPUT_FILE} for FNS Initial Load...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("<FNS_Snapshot>\n")

    # Create Queue Receiver
    durable_exclusive_queue = Queue.durable_exclusive_queue(queue_name)
    receiver = messaging_service.create_persistent_message_receiver_builder().build(durable_exclusive_queue)
    receiver.start()
    
    msg_handler = MessageDumper()
    print(f"Listening on queue: {queue_name}...")
    print(f"Waiting for stream... (Timeout: {TIMEOUT_SECONDS}s, Silence Stop: {SILENCE_TIMEOUT}s)")
    
    # Receive messages
    receiver.receive_async(msg_handler)
    
    start_time = time.time()
    
    try:
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            time_since_last = current_time - msg_handler.last_message_time
            
            # Cases to stop:
            # 1. No messages ever received and TIMEOUT reached.
            if msg_handler.message_count == 0 and elapsed > TIMEOUT_SECONDS:
                print(f"\n[TIMEOUT] No messages received in {TIMEOUT_SECONDS} seconds.")
                break
                
            # 2. Messages received, but silence for SILENCE_TIMEOUT
            if msg_handler.message_count > 0 and time_since_last > SILENCE_TIMEOUT:
                print(f"\n[DONE] Stream ended. No messages for {SILENCE_TIMEOUT} seconds.")
                break
                
            time.sleep(0.5)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Terminating...")
        receiver.terminate()
        messaging_service.disconnect()
        
        # Close Root Tag
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write("</FNS_Snapshot>\n")
            
        print(f"Disconnected. Total messages captured: {msg_handler.message_count}")
        print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
