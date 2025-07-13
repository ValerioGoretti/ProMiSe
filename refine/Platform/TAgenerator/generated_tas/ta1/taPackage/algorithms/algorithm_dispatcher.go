package algorithms

import (
	"fmt"
)

// Tipo comune per tutte le funzioni di processamento
type ProcessingFunc func(inputPath string, outputPath string) error

// Mappa degli algoritmi disponibili
var AlgorithmMap = map[string]ProcessingFunc{
	"AlphaMiner": AlphaMiner,
}

// RunAlgorithm esegue l'algoritmo specificato, se presente nella mappa
func RunAlgorithm(name string, inputPath string, outputPath string, eventMatrix [][]string, configID string) error {
	switch name {
	case "HeuristicMiner":
		return HeuristicMiner(eventMatrix, configID)
	default:
		algo, exists := AlgorithmMap[name]
		if !exists {
			return fmt.Errorf("algoritmo non supportato: %s", name)
		}
		return algo(inputPath, outputPath)
	}
}
