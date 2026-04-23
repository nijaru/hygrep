package main

import (
	"os"
	"strconv"
)

type Config struct {
	Port int
	Env  string
}

func LoadConfig() Config {
	portStr := os.Getenv("PORT")
	port, _ := strconv.Atoi(portStr)
	if port == 0 {
		port = 8080
	}
	env := os.Getenv("APP_ENV")
	if env == "" {
		env = "development"
	}
	return Config{Port: port, Env: env}
}\n