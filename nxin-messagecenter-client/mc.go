package main

import (
	"os"
	"fmt"
	"time"
	"strconv"
	"encoding/hex"
	"encoding/xml"
	"crypto/md5"
	"github.com/astaxie/beego/httplib"
	"errors"
)

type ShortMessage struct {
	SendSort             string `xml:"sendSort"`
	SendType             string `xml:"sendType"`
	IsSwitchChannelRetry int    `xml:"isSwitchChannelRetry"`
	IsGroup              int    `xml:"isGroup"`
	PhoneNumber          string `xml:"phoneNumber"`
	Message              string `xml:"message"`
	Remarks              string `xml:"remarks"`
}

/* Global variables must define by var */
var url = "http://xxxx.nxin.com/message/sendsmsCommonNxin";
var secret = "xxxxx"
var sys_id = ""


func genXml(message string, phones string) string{
	data := &ShortMessage{
		SendSort: "SMS",
		SendType: "COMMON_GROUP",
		IsSwitchChannelRetry: 1,
		IsGroup: 1,
		PhoneNumber: phones,
		Message: message,
		Remarks: sys_id,
	}
	bytes, _ := xml.Marshal(data) // []byte
	return string(bytes)
}

func main() {
	if (len(os.Args) != 3) {
		fmt.Println(errors.New("only support two arguments"))
	}
	message := os.Args[1]
	phones := os.Args[2]

	// timestamp
	timeStamp := time.Now().UnixNano() / int64(time.Millisecond)
	timeStampString := strconv.FormatInt(timeStamp, 10)

	// token
	md5Ctx := md5.New()
	md5Ctx.Write([]byte(secret + timeStampString))
	cipherStr := md5Ctx.Sum(nil)
	token := hex.EncodeToString(cipherStr)

        // do request
	r := httplib.Post(url).SetTimeout(5 * time.Second, 5 * time.Second)
	r.Param("message", genXml(message, phones))
	r.Param("timestamp", timeStampString)
	r.Param("systemId", sys_id)
	r.Param("accessToken", token)
	r.Param("businessChannel", "OTHERS")

	resp, err := r.String()
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(resp)
}
