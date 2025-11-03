#!/usr/bin/env python3
"""
Collect baseline metrics from UAM system runs.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from src.composition_root import ServiceContainer
from src.interfaces.dto import Severity


class BaselineMetricsCollector:
    """Collect and analyze baseline metrics from system runs."""

    def __init__(self):
        self.container = ServiceContainer.production()
        self.metrics = {
            "timestamp": datetime.now().isoformat(),
            "processing_times": {},
            "violation_counts": {},
            "kpi_distributions": {},
            "performance_metrics": {},
            "alert_metrics": {}
        }

    def generate_test_dataset(self, num_apps: int = 100, users_per_app: int = 1000) -> pd.DataFrame:
        """Generate realistic test dataset for baseline testing."""
        print(f"Generating dataset: {num_apps} apps × {users_per_app} users = {num_apps * users_per_app} records")
        
        data = []
        for app_id in range(1, num_apps + 1):
            app_prefix = f"APP-{app_id:03d}"
            
            for user_id in range(1, users_per_app + 1):
                # Simulate realistic access patterns
                is_privileged = user_id <= (users_per_app * 0.1)  # 10% privileged
                has_access = user_id <= (users_per_app * 0.8)  # 80% have access
                
                # Simulate some violations for testing
                failed_attempts = 0
                if user_id % 50 == 0:  # 2% have failed attempts
                    failed_attempts = 3 + (user_id % 5)
                
                # Simulate orphaned accounts
                last_login = None
                if user_id % 100 == 0:  # 1% orphaned
                    last_login = datetime.now() - timedelta(days=90 + (user_id % 30))
                else:
                    last_login = datetime.now() - timedelta(days=user_id % 30)
                
                record = {
                    "app_id": app_prefix,
                    "user_id": f"USER-{user_id:06d}",
                    "is_privileged": is_privileged,
                    "has_access": has_access,
                    "failed_attempts": failed_attempts,
                    "last_login": last_login.isoformat() if last_login else None,
                    "role": "ADMIN" if is_privileged else "USER",
                    "environment": "PROD" if app_id % 4 != 0 else "DEV",
                    "created_at": (datetime.now() - timedelta(days=365)).isoformat(),
                    "justification": "Business need" if is_privileged and user_id % 3 == 0 else None,
                    "last_review_date": (datetime.now() - timedelta(days=user_id % 180)).isoformat() if is_privileged else None
                }
                data.append(record)
        
        return pd.DataFrame(data)

    def measure_processing_pipeline(self, df: pd.DataFrame) -> Dict[str, float]:
        """Measure end-to-end processing pipeline performance."""
        print("Measuring processing pipeline performance...")
        
        start_time = time.time()
        
        # Step 1: CSV Parsing
        csv_parser = self.container.csv_parser()
        parse_start = time.time()
        parsed_data = csv_parser.parse(df)
        parse_time = time.time() - parse_start
        
        # Step 2: KPI Calculation
        kpi_start = time.time()
        kpi_results = []
        for app_id in df["app_id"].unique():
            # Test each KPI calculator
            calc = self.container.orphan_accounts_calculator()
            kpi = calc.compute(df, app_id)
            kpi_results.append(kpi)
        kpi_time = time.time() - kpi_start
        
        # Step 3: Policy Evaluation
        policy_start = time.time()
        policy_engine = self.container.policy_engine()
        violations = []
        for kpi in kpi_results:
            app_violations = policy_engine.evaluate(kpi)
            violations.extend(app_violations)
        policy_time = time.time() - policy_start
        
        # Step 4: Alert Generation
        alert_start = time.time()
        alert_gen = self.container.alert_generator()
        alerts = []
        for violation in violations:
            alert = alert_gen.generate_and_send(violation)
            alerts.append(alert)
        alert_time = time.time() - alert_start
        
        total_time = time.time() - start_time
        
        return {
            "total_processing_time": total_time,
            "parse_time": parse_time,
            "kpi_time": kpi_time,
            "policy_time": policy_time,
            "alert_time": alert_time,
            "records_per_second": len(df) / total_time,
            "apps_processed": len(df["app_id"].unique()),
            "total_records": len(df)
        }

    def analyze_violation_patterns(self, violations: List) -> Dict[str, Any]:
        """Analyze violation patterns and distributions."""
        print("Analyzing violation patterns...")
        
        if not violations:
            return {"total_violations": 0, "message": "No violations found"}
        
        severity_counts = {}
        kpi_violations = {}
        
        for violation in violations:
            # Count by severity
            severity = violation.severity.name if hasattr(violation.severity, 'name') else str(violation.severity)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by KPI type
            for kpi_name in violation.kpi_values.keys():
                kpi_violations[kpi_name] = kpi_violations.get(kpi_name, 0) + 1
        
        return {
            "total_violations": len(violations),
            "severity_distribution": severity_counts,
            "kpi_violation_distribution": kpi_violations,
            "violations_per_app": len(violations) / len(set(v.app_id for v in violations)),
            "critical_violations": severity_counts.get("CRITICAL", 0),
            "high_violations": severity_counts.get("HIGH", 0)
        }

    def collect_kpi_distributions(self, kpi_results: List) -> Dict[str, Any]:
        """Collect KPI value distributions."""
        print("Collecting KPI distributions...")
        
        distributions = {}
        
        for kpi in kpi_results:
            app_id = kpi.app_id
            for kpi_name, value in kpi.kpi_values.items():
                if kpi_name not in distributions:
                    distributions[kpi_name] = []
                distributions[kpi_name].append(value)
        
        # Calculate statistics for each KPI
        stats = {}
        for kpi_name, values in distributions.items():
            if values:
                stats[kpi_name] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "median": sorted(values)[len(values) // 2],
                    "count": len(values),
                    "std_dev": (sum((x - sum(values)/len(values))**2 for x in values) / len(values)) ** 0.5
                }
        
        return stats

    def run_baseline_collection(self, dataset_sizes: List[int] = None) -> Dict[str, Any]:
        """Run complete baseline collection for different dataset sizes."""
        if dataset_sizes is None:
            dataset_sizes = [50, 100, 500]  # Small, medium, larger datasets
        
        print("Starting baseline metrics collection...")
        
        all_results = {
            "collection_timestamp": datetime.now().isoformat(),
            "test_runs": []
        }
        
        for size in dataset_sizes:
            print(f"\n{'='*50}")
            print(f"Testing with dataset size: {size} apps")
            print(f"{'='*50}")
            
            # Generate test data
            df = self.generate_test_dataset(num_apps=size, users_per_app=1000)
            
            # Measure processing
            processing_metrics = self.measure_processing_pipeline(df)
            
            # Get violations for analysis
            policy_engine = self.container.policy_engine()
            calc = self.container.orphan_accounts_calculator()
            violations = []
            kpi_results = []
            
            for app_id in df["app_id"].unique():
                kpi = calc.compute(df, app_id)
                kpi_results.append(kpi)
                app_violations = policy_engine.evaluate(kpi)
                violations.extend(app_violations)
            
            # Analyze patterns
            violation_analysis = self.analyze_violation_patterns(violations)
            kpi_distributions = self.collect_kpi_distributions(kpi_results)
            
            run_result = {
                "dataset_size": size,
                "total_records": len(df),
                "processing_metrics": processing_metrics,
                "violation_analysis": violation_analysis,
                "kpi_distributions": kpi_distributions
            }
            
            all_results["test_runs"].append(run_result)
            
            print(f"✅ Completed {size} apps dataset:")
            print(f"   Processing time: {processing_metrics['total_processing_time']:.2f}s")
            print(f"   Records/sec: {processing_metrics['records_per_second']:.0f}")
            print(f"   Violations: {violation_analysis.get('total_violations', 0)}")
        
        return all_results

    def save_baseline_results(self, results: Dict[str, Any], output_path: str = None):
        """Save baseline results to file."""
        if output_path is None:
            output_path = f"baseline_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_file = Path("metrics") / output_path
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Baseline metrics saved to: {output_file}")
        return output_file


def main():
    """Main execution function."""
    collector = BaselineMetricsCollector()
    
    # Run baseline collection
    results = collector.run_baseline_collection()
    
    # Save results
    output_file = collector.save_baseline_results(results)
    
    # Print summary
    print(f"\n{'='*60}")
    print("BASELINE METRICS SUMMARY")
    print(f"{'='*60}")
    
    for run in results["test_runs"]:
        size = run["dataset_size"]
        proc = run["processing_metrics"]
        violations = run["violation_analysis"]
        
        print(f"\nDataset: {size} apps ({run['total_records']} records)")
        print(f"  Processing Time: {proc['total_processing_time']:.2f}s")
        print(f"  Throughput: {proc['records_per_second']:.0f} records/sec")
        print(f"  Total Violations: {violations.get('total_violations', 0)}")
        print(f"  Critical Violations: {violations.get('critical_violations', 0)}")
        print(f"  High Violations: {violations.get('high_violations', 0)}")


if __name__ == "__main__":
    main()