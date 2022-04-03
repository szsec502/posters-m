package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"
)

func main() {
	target := "http://localhost:5000/api/link"

	client := &http.Client{}

	params := strings.NewReader(`{
"posterId": "2"
	}`)

	req, err := http.NewRequest("POST", target, params)
	if err != nil {
		fmt.Printf("can't create request : %+v\n", err)
		return
	}

	req.Header.Add("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("can't send request : %+v\n", resp)
		return
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("can't read body from response : %v\n", err)
		return
	}

	fmt.Println(body)
}
