#!/usr/bin/env python3
"""
Baseline metrics collection for UAM system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from src.composition_root import ServiceContainer


def generate_test_data(num_apps: int, users_per_app: int) -> pd.DataFrame:
    """Generate test data for baseline testing."""
    data = []
    for app_id in range(1, num_apps + 1):
        app_prefix = f"APP-{app_id:03d}"
        
        for user_id in range(1, users_per_app + 1):
            # Simulate realistic patterns
            is_privileged = user_id <= (users_per_app * 0.1)  # 10% privileged
            has_access = user_id <= (users_per_app * 0.8)  # 80% have access
            
            # Simulate violations
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


def run_baseline_collection():
    """Collect baseline metrics."""
    print("🚀 UAM Baseline Metrics Collection")
    print("=" * 50)
    
    # Initialize test container (no external dependencies)
    container = ServiceContainer.test()
    
    # Test scenarios
    scenarios = [
        ("Small", 10, 100),
        ("Medium", 50, 500), 
        ("Large", 100, 1000)
    ]
    
    results = {
        "collection_timestamp": datetime.now().isoformat(),
        "scenarios": []
    }
    
    for name, num_apps, users_per_app in scenarios:
        print(f"\n📊 Testing {name}: {num_apps} apps × {users_per_app} users")
        
        # Generate test data
        df = generate_test_data(num_apps, users_per_app)
        print(f"   Generated {len(df)} records")
        
        # Measure processing
        start_time = time.time()
        
        # Get components
        csv_parser = container.csv_parser()
        policy_engine = container.policy_engine()
        alert_gen = container.alert_generator()
        
        total_violations = 0
        total_alerts = 0
        
        # Process each app
        for app_id in df["app_id"].unique():
            app_data = df[df["app_id"] == app_id]
            
            # Calculate KPIs
            orphan_calc = container.orphan_accounts_calculator()
            kpi = orphan_calc.compute(app_data, app_id)
            
            # Evaluate policies
            violations = policy_engine.evaluate(app_id, {kpi.kpi_name: kpi.value})
            total_violations += len(violations)
            
            # Generate alerts
            for violation in violations:
                alert = alert_gen.generate_and_send(violation)
                total_alerts += 1
        
        processing_time = time.time() - start_time
        
        scenario_result = {
            "name": name,
            "apps": num_apps,
            "users_per_app": users_per_app,
            "total_records": len(df),
            "processing_time_seconds": round(processing_time, 2),
            "records_per_second": round(len(df) / processing_time, 0),
            "apps_per_second": round(num_apps / processing_time, 1),
            "total_violations": total_violations,
            "total_alerts": total_alerts,
            "violation_rate_percent": round((total_violations / num_apps) * 100, 1) if num_apps > 0 else 0,
            "alerts_per_violation": round(total_alerts / total_violations, 1) if total_violations > 0 else 0
        }
        
        results["scenarios"].append(scenario_result)
        
        print(f"   ✅ Time: {processing_time:.2f}s")
        print(f"   ✅ Speed: {len(df) / processing_time:.0f} records/sec")
        print(f"   ✅ Violations: {total_violations}")
        print(f"   ✅ Alerts: {total_alerts}")
    
    # Save results
    output_dir = Path("metrics")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n📈 BASELINE SUMMARY")
    print("=" * 40)
    
    for scenario in results["scenarios"]:
        print(f"\n{scenario['name']} Dataset:")
        print(f"  Size: {scenario['apps']} apps, {scenario['total_records']} records")
        print(f"  Performance: {scenario['processing_time_seconds']}s")
        print(f"  Throughput: {scenario['records_per_second']} records/sec")
        print(f"  Violations: {scenario['total_violations']} ({scenario['violation_rate_percent']}%)")
        print(f"  Alerts: {scenario['total_alerts']}")
    
    # Performance analysis
    large_scenario = next((s for s in results["scenarios"] if s["name"] == "Large"), None)
    if large_scenario:
        print(f"\n🎯 PERFORMANCE TARGETS")
        print("=" * 30)
        
        records_per_sec = large_scenario["records_per_second"]
        
        # Project to full scale (1,200 apps × 40,000 users = 48M records)
        full_scale_records = 48_000_000
        projected_time = full_scale_records / records_per_sec
        
        print(f"Large Dataset Performance:")
        print(f"  {records_per_sec:.0f} records/second")
        print(f"  {large_scenario['apps_per_second']} apps/second")
        
        print(f"\nFull Scale Projection (48M records):")
        print(f"  Estimated time: {projected_time/60:.1f} minutes")
        
        if projected_time < 900:  # 15 minutes
            print(f"  ✅ MEETS <15 minute target!")
        else:
            print(f"  ⚠️  Exceeds 15 minute target by {(projected_time-900)/60:.1f} minutes")
        
        # Alert dispatch target (<5 minutes)
        avg_time_per_app = large_scenario["processing_time_seconds"] / large_scenario["apps"]
        if avg_time_per_app < 300:  # 5 minutes
            print(f"  ✅ MEETS <5 minute alert dispatch target!")
        else:
            print(f"  ⚠️  Exceeds 5 minute alert dispatch target")
    
    print(f"\n💾 Results saved to: {output_file}")
    return results


if __name__ == "__main__":
    run_baseline_collection()