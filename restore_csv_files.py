import os
import shutil
import glob

def restore_csv_files(backup_dir):
    if not os.path.exists(backup_dir):
        print(f"Error: Backup directory '{backup_dir}' does not exist.")
        return

    # Get all CSV files in the backup directory and its subdirectories
    backup_files = glob.glob(os.path.join(backup_dir, '**', '*.csv'), recursive=True)

    for backup_file in backup_files:
        # Get the relative path of the file within the backup directory
        relative_path = os.path.relpath(backup_file, backup_dir)
        
        # Construct the original file path
        original_file = os.path.join(os.getcwd(), relative_path)
        
        # Ensure the directory for the original file exists
        os.makedirs(os.path.dirname(original_file), exist_ok=True)
        
        # Copy the backup file to the original location
        shutil.copy2(backup_file, original_file)
        print(f"Restored: {original_file}")

    print(f"Restore completed. Files restored from '{backup_dir}' directory.")

if __name__ == '__main__':
    # Get the latest backup directory
    backup_dirs = glob.glob('csv_backup_*')
    if not backup_dirs:
        print("Error: No backup directories found.")
    else:
        latest_backup = max(backup_dirs, key=os.path.getctime)
        print(f"Restoring from the latest backup: {latest_backup}")
        restore_csv_files(latest_backup)