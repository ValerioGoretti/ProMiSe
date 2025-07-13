package config

import (
	"encoding/xml"
	"fmt"
	"os"
	"strings"
	"time"
)

// Definizioni strutture XES base per parsing

type XesEvent struct {
	Strings []XesAttribute `xml:"string"`
	Dates   []XesAttribute `xml:"date"`
	// Combiniamo string+date come attributi generici
}

type XesTrace struct {
	Attributes []XesAttribute `xml:"string"`
	Events     []XesEvent     `xml:"event"`
}

type XesLog struct {
	Traces []XesTrace `xml:"trace"`
}

type XesAttribute struct {
	Key   string `xml:"key,attr"`
	Value string `xml:"value,attr"`
}

type FilteredEvent struct {
	Attributes []XesAttribute `json:"Attributes"`
	Date       string         `json:"Date"` // Timestamp rilevante, se presente
}

type FilteredTrace struct {
	Attributes []XesAttribute  `json:"Attributes"`
	Events     []FilteredEvent `json:"Events"`
}

type FilteredLog struct {
	Traces []FilteredTrace `json:"Traces"`
}

// Funzione principale
func LoadAndFilterXesLog(filePath string, rules LogUsageRules) (*FilteredLog, error) {
	fmt.Println("[DEBUG] LoadAndFilterXesLog -> ENTRATO con filePath:", filePath)
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open xes file: %w", err)
	}
	defer file.Close()

	var log XesLog
	decoder := xml.NewDecoder(file)
	if err := decoder.Decode(&log); err != nil {
		return nil, fmt.Errorf("failed to parse xes xml: %w", err)
	}

	filteredLog := &FilteredLog{}

	for _, trace := range log.Traces {
		filteredTrace := FilteredTrace{
			Attributes: trace.Attributes,
			Events:     []FilteredEvent{},
		}

		containsMustInclude := false
		containsMustExclude := false

		for _, event := range trace.Events {
			// Unifica string e date
			allAttrs := append(event.Strings, event.Dates...)

			conceptName := GetAttributeValue(allAttrs, rules.AttributeExclusionRules.EventAttribute)

			// AttributeExclusionRules
			if stringInSlice(conceptName, rules.AttributeExclusionRules.ExcludedAttributes) {
				continue
			}

			// allowedTimeRange
			timeValStr := GetAttributeValue(allAttrs, rules.AllowedTimeRange.EventAttribute)
			if timeValStr != "" {
				tm, err := time.Parse(time.RFC3339, timeValStr)
				if err == nil {
					if tm.Before(rules.AllowedTimeRange.StartDate) || tm.After(rules.AllowedTimeRange.EndDate) {
						continue
					}
				}
			}

			// Semantic constraints
			if stringInSlice(conceptName, rules.SemanticLogConstraints.MustInclude) {
				containsMustInclude = true
			}
			if stringInSlice(conceptName, rules.SemanticLogConstraints.MustExclude) {
				containsMustExclude = true
			}

			filteredTrace.Events = append(filteredTrace.Events, FilteredEvent{
				Attributes: allAttrs,
				Date:       timeValStr,
			})
		}

		if containsMustInclude && !containsMustExclude && len(filteredTrace.Events) > 0 {
			filteredLog.Traces = append(filteredLog.Traces, filteredTrace)
		}
	}

	return filteredLog, nil
}

func GetAttributeValue(attrs []XesAttribute, key string) string {
	for _, a := range attrs {
		if strings.ToLower(a.Key) == strings.ToLower(key) {
			return a.Value
		}
	}
	return ""
}

func stringInSlice(s string, list []string) bool {
	for _, v := range list {
		if v == s {
			return true
		}
	}
	return false
}
