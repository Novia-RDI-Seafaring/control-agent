from pydantic_evals.reporting import EvaluationReport, ReportCase, EvaluationResult
from typing import Dict, Any
from devtools import debug
from time import time
from pathlib import Path
import json


def render_report(report: EvaluationReport, key:str):
    print(f"============={report.name}=============\n\n")
    for case in report.cases:
        print(f"\n\nCase: {case.name}\n")
        print("======================")
        print("Inputs: ", case.inputs)
        if case.expected_output:
            print("\tExpected output:", case.expected_output)
        print("Assertions:")
        for name, assertion in case.assertions.items():
            print("\t", "✅" if assertion.value else "❌", assertion.name, ":", assertion.reason[:40] + "..." if len(str(assertion.reason)) > 40 else assertion.reason)    
        #print("Output: ", case.output)
        print("\n")

                
def save_report(key:str, report: EvaluationReport):
    return
    path = Path("data/reports")
    path.mkdir(parents=True, exist_ok=True) 
    from dataclasses import asdict, is_dataclass

    
    report_dict = asdict(report)
    with open(path / f"{key}-{time.time()}.json", "w") as f:
        json.dump(report_dict, f, indent=4, default=str)
        print(report)
    print(f"Wrote {key} report to {path / f'{key}.json'}")


def test_render():
    pass
    

if __name__ == "__main__":
    test_render()