package main

import (
	"crypto/md5"
	"encoding/hex"
	"encoding/xml"
	"errors"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strconv"
	"time"
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
var api = "http://xxxx.nxin.com/message/sendsmsCommonNxin"
var secret = "xxxx"
var sys_id = ""

func genXml(message string, phones string) string {
	data := &ShortMessage{
		SendSort:             "SMS",
		SendType:             "COMMON_GROUP",
		IsSwitchChannelRetry: 1,
		IsGroup:              1,
		PhoneNumber:          phones,
		Message:              message,
		Remarks:              sys_id,
	}
	bytes, _ := xml.Marshal(data) // []byte
	return string(bytes)
}

func sendSmsMessage(message string, phones string, debug bool) {
	client := http.Client{
		Timeout: time.Duration(5 * time.Second),
	}

	// timestamp
	timeStamp := time.Now().UnixNano() / int64(time.Millisecond)
	timeStampString := strconv.FormatInt(timeStamp, 10)

	// token
	md5Ctx := md5.New()
	md5Ctx.Write([]byte(secret + timeStampString))
	cipherStr := md5Ctx.Sum(nil)
	token := hex.EncodeToString(cipherStr)

	req, err := http.NewRequest("POST", api, nil)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	query := req.URL.Query()
	query.Add("message", genXml(message, phones))
	query.Add("timestamp", timeStampString)
	query.Add("systemId", sys_id)
	query.Add("accessToken", token)
	query.Add("businessChannel", "OTHERS")
	req.URL.RawQuery = query.Encode()
	if debug {
		println(req.URL.String())
	}

	resp, err := client.Do(req)
	if err != nil {
		fmt.Println(err)
	}
	defer resp.Body.Close()
	resp_body, _ := ioutil.ReadAll(resp.Body)
	fmt.Println(string(resp_body))
}

func main() {
	args_len := len(os.Args)
	if args_len < 3 || args_len > 4 {
		fmt.Println(errors.New("only support two or three arguments"))
		os.Exit(1)
	}
	message := os.Args[1]
	phones := os.Args[2]
	debug := false
	if args_len == 4 {
		debug = true
	}
	sendSmsMessage(message, phones, debug)
}
