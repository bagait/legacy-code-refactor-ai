# legacy_code_example.py
# A script that processes user and order data from a CSV file.
# This is a monolithic script with poor separation of concerns, making it a perfect candidate for refactoring.

import csv
import json

def process_data_monolith(input_file, output_file_json, output_file_csv):
    """
    Reads user and order data, calculates total order value per user,
    filters for high-value users, and writes reports in two formats.
    """
    print(f"Starting data processing for {input_file}...")

    # 1. Read data from CSV
    records = []
    try:
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
        return

    print(f"Read {len(records)} records.")

    # 2. Process data: aggregate order values
    user_orders = {}
    for record in records:
        user_id = record['user_id']
        try:
            order_value = float(record['order_value'])
        except (ValueError, TypeError):
            continue # Skip malformed records

        if user_id not in user_orders:
            user_orders[user_id] = 0
        user_orders[user_id] += order_value

    print("Aggregated order values for users.")

    # 3. Business Logic: filter for high-value users
    high_value_threshold = 1000.0
    high_value_users = {
        user_id: total
        for user_id, total in user_orders.items()
        if total > high_value_threshold
    }
    print(f"Found {len(high_value_users)} high-value users.")

    # 4. Write JSON report
    report_data = {
        'high_value_users': high_value_users,
        'user_count': len(high_value_users)
    }
    try:
        with open(output_file_json, 'w') as f:
            json.dump(report_data, f, indent=4)
        print(f"JSON report written to {output_file_json}")
    except IOError:
        print(f"Error writing to {output_file_json}")


    # 5. Write CSV report
    try:
        with open(output_file_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'total_order_value'])
            for user_id, total in high_value_users.items():
                writer.writerow([user_id, total])
        print(f"CSV report written to {output_file_csv}")
    except IOError:
        print(f"Error writing to {output_file_csv}")


if __name__ == "__main__":
    # Create dummy data for demonstration
    with open("data.csv", "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'order_id', 'order_value'])
        writer.writerow(['user1', 'a001', '500.50'])
        writer.writerow(['user2', 'a002', '250.00'])
        writer.writerow(['user1', 'a003', '750.25'])
        writer.writerow(['user3', 'a004', '100.00'])
        writer.writerow(['user2', 'a005', '1200.00'])

    process_data_monolith("data.csv", "report.json", "report.csv")
