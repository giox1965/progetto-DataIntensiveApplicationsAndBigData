FROM confluentinc/cp-kafka-connect-base:latest

RUN confluent-hub install --no-prompt mongodb/kafka-connect-mongodb:latest

COPY entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]