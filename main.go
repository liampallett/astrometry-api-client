package main

import (
	"fmt"
	"os"
)

func main() {
	API_KEY := os.Getenv("ASTROMETRY_API_KEY")
	fmt.Println(API_KEY)
}
