package main

import (
	"fmt"
	"os"
	"github.com/robertkrimen/otto/xes"
)

type EventLog [][]string

type Relation int

const (
	None Relation = iota
	Causal
	Parallel
)

type AlphaMiner struct {
	log       EventLog
	relations map[string]map[string]Relation
}

func NewAlphaMiner(log EventLog) *AlphaMiner {
	return &AlphaMiner{
		log:       log,
		relations:  make(map[string]map[string]Relation),
	}
}

func (am *AlphaMiner) ComputeRelations() {
	for _, trace := range am.log {
		for i, a := range trace {
			if _, exists := am.relations[a]; !exists {
				am.relations[a] = make(map[string]Relation)
			}
			for j := i + 1; j < len(trace); j++ {
				b := trace[j]
				if _, exists := am.relations[b]; !exists {
					am.relations[b] = make(map[string]Relation)
				}
				if am.relations[a][b] == None {
					am.relations[a][b] = Causal
				}
				if am.relations[b][a] == Causal {
					am.relations[a][b] = Parallel
					am.relations[b][a] = Parallel
				}
			}
		}
	}
}

func (am *AlphaMiner) PrintRelations() {
	for a, relMap := range am.relations {
		for b, rel := range relMap {
			var relationStr string
			switch rel {
			case Causal:
				relationStr = ">"
			case Parallel:
				relationStr = "||"
			default:
				relationStr = "#"
			}
			fmt.Printf("%s %s %s\n", a, relationStr, b)
		}
	}
}

func ReadXESFile(filename string) (EventLog, error) {
	log := EventLog{}
	xesLog, err := xes.Load(filename)
	if err != nil {
		return nil, err
	}
	for _, trace := range xesLog.Traces {
		var eventTrace []string
		for _, event := range trace.Events {
			eventTrace = append(eventTrace, event.Name)
		}
		log = append(log, eventTrace)
	}
	return log, nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run main.go <eventlog.xes>")
		return
	}
	filename := os.Args[1]
	log, err := ReadXESFile(filename)
	if err != nil {
		fmt.Println("Error reading XES file:", err)
		return
	}

	miner := NewAlphaMiner(log)
	miner.ComputeRelations()
	miner.PrintRelations()
}
