import java.security.MessageDigest
import java.nio.charset.StandardCharsets
import groovy.xml.StreamingMarkupBuilder

/**
 * author liuyang
 */


def domain = "XXXX.nxin.com"
api = "http://$domain/message/sendsmsCommonNxin"
secret = "XXXX"
sys_id = 123456

static readInputStream(InputStream stream) {
    BufferedReader br = new BufferedReader(new InputStreamReader(stream))
    StringBuffer sb = new StringBuffer()
    String line
    while ((line = br.readLine()) != null) {
        sb.append(line)
    }
    sb.toString()
}

def genXml(String msgText, String phones) {
    def xml = new StreamingMarkupBuilder().bind {
        ShortMessage() {
            sendSort("SMS")
            sendType("COMMON_GROUP")
            isGroup("1")
            phoneNumber(phones)
            isSwitchChannelRetry("1")
            message(msgText)
            remarks(sys_id)
        }
    }
    URLEncoder.encode(xml.toString(), StandardCharsets.UTF_8.name())
}


def send_sms_message(String msgText, String phones, boolean debug) {
    def timestamp = new Date().getTime()
    def token = MessageDigest.getInstance("MD5").digest((secret + timestamp).bytes).encodeHex().toString()
    def xml = genXml(msgText, phones)
    new URL(api + "?message=$xml&timestamp=$timestamp&systemId=$sys_id&accessToken=$token&businessChannel=OTHERS").openConnection().with {
        setDoOutput(true) // POST
        setRequestMethod("POST")
        setRequestProperty("Accept-Charset", "UTF-8")

        if (debug) { println(getURL().path)}

        def code = getResponseCode()
        if (code <= 299 && code >= 200) {
            println(readInputStream(getInputStream()))
        } else {
            println("code: $code, msg: ${getResponseMessage()}")
        }

    }
}

send_sms_message("groovy testing 短信发送", "138********", false)
