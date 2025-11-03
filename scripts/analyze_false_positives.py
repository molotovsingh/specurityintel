#!/usr/bin/env python3
"""
Analyze false positive rates in UAM system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.composition_root import ServiceContainer
from src.interfaces.dto import Severity


def generate_violation_scenarios():
    """Generate test scenarios with known true/false violations."""
    
    scenarios = [
        # True violations (should be detected)
        {
            "name": "High Orphaned Accounts",
            "app_id": "APP-TRUE-001",
            "data": {
                "orphan_accounts": 15,  # Above threshold (10)
                "privileged_accounts": 5,
                "failed_access_attempts": 2
            },
            "expected_violations": True,
            "expected_severity": "HIGH"
        },
        {
            "name": "Critical Failed Access",
            "app_id": "APP-TRUE-002", 
            "data": {
                "orphan_accounts": 3,
                "privileged_accounts": 8,
                "failed_access_attempts": 25  # Above threshold (20)
            },
            "expected_violations": True,
            "expected_severity": "CRITICAL"
        },
        {
            "name": "Medium Privileged without Review",
            "app_id": "APP-TRUE-003",
            "data": {
                "orphan_accounts": 2,
                "privileged_accounts": 12,  # Above threshold (10)
                "failed_access_attempts": 1
            },
            "expected_violations": True,
            "expected_severity": "MEDIUM"
        },
        
        # False positives (should NOT be detected)
        {
            "name": "Normal Operations",
            "app_id": "APP-FALSE-001",
            "data": {
                "orphan_accounts": 2,  # Below threshold
                "privileged_accounts": 3,  # Below threshold
                "failed_access_attempts": 1  # Below threshold
            },
            "expected_violations": False,
            "expected_severity": None
        },
        {
            "name": "Low Risk Environment",
            "app_id": "APP-FALSE-002",
            "data": {
                "orphan_accounts": 5,  # Below critical threshold
                "privileged_accounts": 6,  # Below critical threshold
                "failed_access_attempts": 8  # Below critical threshold
            },
            "expected_violations": False,
            "expected_severity": None
        },
        {
            "name": "Compliant Access",
            "app_id": "APP-FALSE-003",
            "data": {
                "orphan_accounts": 1,
                "privileged_accounts": 2,
                "failed_access_attempts": 0
            },
            "expected_violations": False,
            "expected_severity": None
        }
    ]
    
    return scenarios


def analyze_false_positive_rate():
    """Analyze false positive rate of the system."""
    print("🔍 Analyzing False Positive Rates")
    print("=" * 50)
    
    # Initialize test container
    container = ServiceContainer.test()
    policy_engine = container.policy_engine()
    
    # Generate test scenarios
    scenarios = generate_violation_scenarios()
    
    results = {
        "analysis_timestamp": datetime.now().isoformat(),
        "total_scenarios": len(scenarios),
        "true_violations": 0,
        "false_negatives": 0,
        "false_positives": 0,
        "true_negatives": 0,
        "scenarios": []
    }
    
    print(f"Testing {len(scenarios)} scenarios...")
    
    for scenario in scenarios:
        app_id = scenario["app_id"]
        kpi_data = scenario["data"]
        expected_violations = scenario["expected_violations"]
        expected_severity = scenario["expected_severity"]
        
        # Evaluate through policy engine
        violations = policy_engine.evaluate(app_id, kpi_data)
        
        # Determine result
        has_violations = len(violations) > 0
        actual_severity = violations[0].severity.name if violations else None
        
        # Classify result
        if expected_violations and has_violations:
            result_type = "TRUE_POSITIVE"
            results["true_violations"] += 1
        elif expected_violations and not has_violations:
            result_type = "FALSE_NEGATIVE"
            results["false_negatives"] += 1
        elif not expected_violations and has_violations:
            result_type = "FALSE_POSITIVE"
            results["false_positives"] += 1
        else:
            result_type = "TRUE_NEGATIVE"
            results["true_negatives"] += 1
        
        scenario_result = {
            "name": scenario["name"],
            "app_id": app_id,
            "kpi_data": kpi_data,
            "expected_violations": expected_violations,
            "expected_severity": expected_severity,
            "actual_violations": has_violations,
            "actual_severity": actual_severity,
            "result_type": result_type,
            "violation_count": len(violations),
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity.name,
                    "kpi_values": v.kpi_values
                } for v in violations
            ]
        }
        
        results["scenarios"].append(scenario_result)
        
        # Print scenario result
        status_icon = "✅" if result_type in ["TRUE_POSITIVE", "TRUE_NEGATIVE"] else "❌"
        print(f"  {status_icon} {scenario['name']}: {result_type}")
        
        if violations:
            for v in violations:
                print(f"      → {v.severity.name}: {v.rule_id}")
    
    # Calculate metrics
    tp = results["true_violations"]
    fp = results["false_positives"]
    tn = results["true_negatives"]
    fn = results["false_negatives"]
    
    total = tp + fp + tn + fn
    
    if total > 0:
        results["metrics"] = {
            "accuracy": (tp + tn) / total,
            "precision": tp / (tp + fp) if (tp + fp) > 0 else 0,
            "recall": tp / (tp + fn) if (tp + fn) > 0 else 0,
            "false_positive_rate": fp / (fp + tn) if (fp + tn) > 0 else 0,
            "false_negative_rate": fn / (tp + fn) if (tp + fn) > 0 else 0,
            "true_positive_rate": tp / (tp + fn) if (tp + fn) > 0 else 0,
            "true_negative_rate": tn / (fp + tn) if (fp + tn) > 0 else 0
        }
    else:
        results["metrics"] = {}
    
    # Print analysis
    print(f"\n📊 FALSE POSITIVE ANALYSIS RESULTS")
    print("=" * 50)
    
    print(f"Total Scenarios: {total}")
    print(f"True Positives: {tp} ✅")
    print(f"True Negatives: {tn} ✅")
    print(f"False Positives: {fp} ❌")
    print(f"False Negatives: {fn} ❌")
    
    if results["metrics"]:
        metrics = results["metrics"]
        print(f"\n📈 PERFORMANCE METRICS:")
        print(f"  Accuracy: {metrics['accuracy']:.1%}")
        print(f"  Precision: {metrics['precision']:.1%}")
        print(f"  Recall: {metrics['recall']:.1%}")
        print(f"  False Positive Rate: {metrics['false_positive_rate']:.1%}")
        print(f"  False Negative Rate: {metrics['false_negative_rate']:.1%}")
        
        # Check targets
        print(f"\n🎯 TARGET ANALYSIS:")
        if metrics['false_positive_rate'] <= 0.10:  # 10% target
            print(f"  ✅ False positive rate ({metrics['false_positive_rate']:.1%}) MEETS <10% target!")
        else:
            print(f"  ⚠️  False positive rate ({metrics['false_positive_rate']:.1%}) EXCEEDS 10% target")
        
        if metrics['recall'] >= 0.90:  # 90% recall target
            print(f"  ✅ Recall ({metrics['recall']:.1%}) MEETS >90% target!")
        else:
            print(f"  ⚠️  Recall ({metrics['recall']:.1%}) BELOW 90% target")
    
    # Save results
    output_dir = Path("metrics")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"false_positive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return results


def recommend_threshold_adjustments(results):
    """Recommend threshold adjustments based on analysis."""
    print(f"\n💡 THRESHOLD ADJUSTMENT RECOMMENDATIONS")
    print("=" * 50)
    
    if not results.get("metrics"):
        print("No metrics available for recommendations.")
        return
    
    metrics = results["metrics"]
    fp_rate = metrics["false_positive_rate"]
    fn_rate = metrics["false_negative_rate"]
    
    recommendations = []
    
    if fp_rate > 0.10:
        recommendations.append({
            "issue": "High false positive rate",
            "current_rate": f"{fp_rate:.1%}",
            "recommendation": "Increase threshold values by 10-20% to reduce false positives",
            "affected_kpis": ["orphan_accounts", "privileged_accounts", "failed_access_attempts"]
        })
    
    if fn_rate > 0.10:
        recommendations.append({
            "issue": "High false negative rate", 
            "current_rate": f"{fn_rate:.1%}",
            "recommendation": "Decrease threshold values by 10-20% to catch more violations",
            "affected_kpis": ["orphan_accounts", "privileged_accounts", "failed_access_attempts"]
        })
    
    if fp_rate <= 0.05 and fn_rate <= 0.05:
        recommendations.append({
            "issue": "Excellent performance",
            "current_rates": f"FP: {fp_rate:.1%}, FN: {fn_rate:.1%}",
            "recommendation": "Current thresholds are well-calibrated. Monitor for drift.",
            "affected_kpis": []
        })
    
    if not recommendations:
        recommendations.append({
            "issue": "Performance needs optimization",
            "current_rates": f"FP: {fp_rate:.1%}, FN: {fn_rate:.1%}",
            "recommendation": "Consider separate thresholds for different environments (prod vs dev)",
            "affected_kpis": ["all"]
        })
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['issue']}")
        print(f"   Current: {rec.get('current_rates', rec.get('current_rate', 'N/A'))}")
        print(f"   Action: {rec['recommendation']}")
        if rec['affected_kpis']:
            print(f"   Impact: {', '.join(rec['affected_kpis'])}")


def main():
    """Main execution."""
    results = analyze_false_positive_rate()
    recommend_threshold_adjustments(results)


if __name__ == "__main__":
    main()