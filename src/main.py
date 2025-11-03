"""
Main Entry Point for UAM Compliance Intelligence System.

Runs daily processing pipeline:
1. Parse CSV file
2. Calculate KPIs
3. Evaluate policies
4. Analyze risks
5. Generate and send alerts
"""

import sys
from pathlib import Path
from .composition_root import ServiceContainer


def main():
    """Main pipeline execution."""
    try:
        # Initialize services
        container = ServiceContainer.production()

        # Get pipeline components
        csv_parser = container.csv_parser()
        policy_engine = container.policy_engine()
        alert_gen = container.alert_generator()

        # Parse input CSV
        csv_path = Path("./data/uam_export.csv")
        if not csv_path.exists():
            print(f"Error: CSV file not found at {csv_path}")
            return 1

        print(f"Parsing CSV from {csv_path}...")
        df, is_full_load = csv_parser.parse(str(csv_path))
        print(f"Loaded {len(df)} records (full_load={is_full_load})")

        # Process each application
        app_ids = df["app_id"].unique() if "app_id" in df.columns else []
        total_violations = 0
        total_alerts = 0

        for app_id in app_ids[:10]:  # Process first 10 apps for demo
            # Step 1: Calculate KPIs
            kpi_values = {}
            try:
                orphan_calc = container.orphan_accounts_calculator()
                kpi = orphan_calc.compute(df, str(app_id))
                kpi_values["orphan_accounts"] = kpi.value
            except Exception as e:
                print(f"KPI computation failed for {app_id}: {e}")

            # Step 2: Evaluate policies
            try:
                violations = policy_engine.evaluate(str(app_id), kpi_values)
                total_violations += len(violations)

                # Step 3-5: For each violation, analyze and alert
                for violation in violations:
                    try:
                        alert = alert_gen.generate_and_send(violation)
                        total_alerts += 1
                        print(f"Alert sent for {app_id}: {alert.alert_id}")
                    except Exception as e:
                        print(f"Alert generation failed: {e}")

            except Exception as e:
                print(f"Policy evaluation failed for {app_id}: {e}")

        print("\nProcessing complete:")
        print(f"  Violations detected: {total_violations}")
        print(f"  Alerts sent: {total_alerts}")

        return 0

    except Exception as e:
        print(f"Pipeline error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
