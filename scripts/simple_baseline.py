#!/usr/bin/env python3
"""
Simple baseline metrics collection.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import json
from datetime import datetime
from pathlib import Path


def run_baseline_test():
    """Run a simple baseline test."""
    print("🚀 Starting UAM Baseline Metrics Collection")
    print("=" * 50)
    
    # Test with sample data
    from tests.integration.test_pipeline import TestEndToEndPipeline
    
    # Create test instance
    test_pipeline = TestEndToEndPipeline()
    test_pipeline.setup_method()
    
    # Run multiple test scenarios
    scenarios = [
        ("Small Dataset", 10, 100),
        ("Medium Dataset", 50, 500), 
        ("Large Dataset", 100, 1000)
    ]
    
    results = {
        "baseline_timestamp": datetime.now().isoformat(),
        "scenarios": []
    }
    
    for name, num_apps, num_users in scenarios:
        print(f"\n📊 Testing {name}: {num_apps} apps × {num_users} users")
        
        # Generate test data
        df = test_pipeline.generate_test_data(num_apps, num_users)
        
        # Measure processing time
        start_time = time.time()
        
        # Process through pipeline
        csv_parser = test_pipeline.test_container.csv_parser()
        policy_engine = test_pipeline.test_container.policy_engine()
        alert_gen = test_pipeline.test_container.alert_generator()
        
        total_violations = 0
        total_alerts = 0
        
        for app_id in df["app_id"].unique():
            # Parse data for this app
            app_data = df[df["app_id"] == app_id]
            
            # Calculate KPIs (simplified)
            orphan_calc = test_pipeline.test_container.orphan_accounts_calculator()
            kpi = orphan_calc.compute(app_data, app_id)
            
            # Evaluate policies
            violations = policy_engine.evaluate(kpi)
            total_violations += len(violations)
            
            # Generate alerts
            for violation in violations:
                alert = alert_gen.generate_and_send(violation)
                total_alerts += 1
        
        processing_time = time.time() - start_time
        
        scenario_result = {
            "name": name,
            "apps": num_apps,
            "users_per_app": num_users,
            "total_records": len(df),
            "processing_time_seconds": round(processing_time, 2),
            "records_per_second": round(len(df) / processing_time, 0),
            "total_violations": total_violations,
            "total_alerts": total_alerts,
            "violation_rate_percent": round((total_violations / num_apps) * 100, 1) if num_apps > 0 else 0
        }
        
        results["scenarios"].append(scenario_result)
        
        print(f"  ✅ Processing time: {processing_time:.2f}s")
        print(f"  ✅ Throughput: {len(df) / processing_time:.0f} records/sec")
        print(f"  ✅ Violations: {total_violations}")
        print(f"  ✅ Alerts: {total_alerts}")
    
    # Save results
    output_dir = Path("metrics")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📈 Baseline Results Summary:")
    print("=" * 40)
    
    for scenario in results["scenarios"]:
        print(f"\n{scenario['name']}:")
        print(f"  Dataset: {scenario['apps']} apps, {scenario['total_records']} records")
        print(f"  Performance: {scenario['processing_time_seconds']}s, {scenario['records_per_second']} records/sec")
        print(f"  Violations: {scenario['total_violations']} ({scenario['violation_rate_percent']}%)")
        print(f"  Alerts: {scenario['total_alerts']}")
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Performance analysis
    print(f"\n📊 Performance Analysis:")
    print("=" * 30)
    
    large_scenario = next((s for s in results["scenarios"] if s["name"] == "Large Dataset"), None)
    if large_scenario:
        records_per_sec = large_scenario["records_per_second"]
        apps_per_sec = large_scenario["apps"] / large_scenario["processing_time_seconds"]
        
        print(f"Large Dataset Performance:")
        print(f"  {records_per_sec:.0f} records/second")
        print(f"  {apps_per_sec:.1f} apps/second")
        
        # Project to full scale (1,200 apps × 40,000 users = 48M records)
        projected_time = 48_000_000 / records_per_sec
        print(f"\nProjected Full Scale (48M records):")
        print(f"  Estimated time: {projected_time/60:.1f} minutes")
        
        if projected_time < 900:  # 15 minutes
            print(f"  ✅ Meets <15 minute target!")
        else:
            print(f"  ⚠️  Exceeds 15 minute target")
    
    return results


if __name__ == "__main__":
    run_baseline_test()