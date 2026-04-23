package main

import (
	"net/http"
	"github.com/gorilla/mux"
)

func SetupRouter() *mux.Router {
	r := mux.NewRouter()
	r.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}).Methods("GET")
	return r
}\n