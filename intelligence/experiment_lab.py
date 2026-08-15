"""Phase 14: safe experiment/simulation registry."""
from dataclasses import dataclass

@dataclass
class Experiment:
    name: str
    domain: str
    parameters: dict
    observations: list[str]

class ExperimentLab:
    def run(self, name: str, domain: str, parameters: dict, simulator):
        result = simulator(parameters)
        return Experiment(name, domain, parameters, [str(result)])
