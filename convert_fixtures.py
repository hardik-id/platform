import os
import sys
import json
import csv
import django

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))  # changed to use current directory
sys.path.append(project_root)

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.common.settings")
django.setup()

from django.apps import apps

def convert_json_to_csv(json_path, csv_path):
    with open(json_path, 'r') as json_file:
        data = json.load(json_file)

    if not data:
        print(f"No data found in {json_path}")
        return

    # Get all field names
    fields = set()
    for item in data:
        fields.update(item['fields'].keys())
    fields = sorted(fields)

    with open(csv_path, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=['id'] + fields)
        writer.writeheader()

        for item in data:
            row = {'id': item['pk']}
            row.update(item['fields'])
            writer.writerow(row)

    print(f"Converted {json_path} to {csv_path}")

def main():
    apps_directory = os.path.join(project_root, 'apps')  # This should now correctly point to /platform/apps
    
    if not os.path.exists(apps_directory):
        print(f"Apps directory does not exist: {apps_directory}")
        return
    
    # Iterate over each app directory in 'apps'
    for app_name in os.listdir(apps_directory):
        app_dir = os.path.join(apps_directory, app_name)
        
        # Look for the fixtures directory within the app
        json_fixture_dir = os.path.join(app_dir, 'fixtures')
        
        if not os.path.exists(json_fixture_dir):
            print(f"No fixtures directory found in: {json_fixture_dir}")
            continue

        csv_fixture_dir = os.path.join(json_fixture_dir, 'csv')
        os.makedirs(csv_fixture_dir, exist_ok=True)

        # Process all JSON files in the fixtures directory
        for filename in os.listdir(json_fixture_dir):
            if filename.endswith('.json'):
                json_path = os.path.join(json_fixture_dir, filename)
                csv_filename = os.path.splitext(filename)[0] + '.csv'
                csv_path = os.path.join(csv_fixture_dir, csv_filename)

                print(f"Converting {json_path} to {csv_path}")
                convert_json_to_csv(json_path, csv_path)

if __name__ == "__main__":
    main()
    print("Conversion completed.")
