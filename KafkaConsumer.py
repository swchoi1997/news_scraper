from confluent_kafka import Consumer, KafkaException
import threading
import time

class KafkaConsumer:
    def __init__(self, kafka_config: dict, topic: str, process_message_callback):
        """
        Kafka 메시지를 읽는 클래스 초기화

        :param kafka_config: Kafka Consumer 설정
        :param topic: 구독할 Kafka 토픽
        :param process_message_callback: 메시지 처리 콜백 함수
        """
        self.kafka_config = kafka_config
        self.topic = topic
        self.process_message_callback = process_message_callback
        self.running = True
        self.consumer = Consumer(self.kafka_config)

    def start(self):
        """
        Kafka 메시지 소비 실행
        """
        try:
            self.consumer.subscribe([self.topic])
            print(f"KafkaReader: Subscribed to topic {self.topic}")

            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:  # 타임아웃
                    continue

                if msg.error():
                    if msg.error().is_eof():
                        print(f"KafkaReader: End of partition reached {msg.topic()} [{msg.partition()}]")
                    else:
                        raise KafkaException(msg.error())
                else:
                    # 메시지 처리 콜백 호출
                    self.process_message_callback(msg.value().decode('utf-8'))
        finally:
            self.consumer.close()

    def stop(self):
        """
        Kafka 소비 중단
        """
        self.running = False


# Kafka 설정
kafka_settings = {
    'bootstrap.servers': '127.0.0.1:20000,127.0.0.1:20001,127.0.0.1:20002',  # 브로커 리스트
    'group.id': 'my_consumer_group',  # Consumer Group ID
    'auto.offset.reset': 'earliest',  # 처음부터 읽기 시작
}


# 메시지 처리 콜백 함수
def process_message(message):
    print(f"Received message: {message}")


# KafkaReader 실행 함수
def run_kafka_reader(reader: KafkaConsumer):
    reader.start()


if __name__ == "__main__":
    topic_nm = "my_test_topic"
    kafka_reader = KafkaConsumer(kafka_settings, topic_nm, process_message)

    # 스레드 생성 및 실행
    kafka_thread = threading.Thread(target=run_kafka_reader, args=(kafka_reader,))
    kafka_thread.start()

    try:
        while True:
            time.sleep(1)  # 메인 스레드 유지
    except KeyboardInterrupt:
        print("Stopping Kafka reader...")
        kafka_reader.stop()
        kafka_thread.join()
