import javax.jms.Session
import javax.jms.TextMessage

import org.apache.activemq.ActiveMQConnectionFactory

def urls = "tcp://ip1:61616,tcp://ip2:61616,tcp://ip3:61616"
def brokerUrl = "failover:($urls)?initialReconnectDelay=1000&maxReconnectAttempts=2"

new ActiveMQConnectionFactory(brokerURL: brokerUrl).createConnection().with {
    start()
    createSession(false, Session.AUTO_ACKNOWLEDGE).with {
        createProducer(createQueue("test.queue")).send(createTextMessage("test message"))
    }
    close()
}
