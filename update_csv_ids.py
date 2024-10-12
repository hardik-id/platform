import csv
import uuid
import base58
import os
from collections import defaultdict

# Use the provided namespace
NAMESPACE = uuid.UUID("bc7980a8-5d44-4ba6-872c-b3c5a0fe763b")

def generate_base58_uuidv5(name):
    # Generate a UUIDv4 for this record
    record_uuid = uuid.uuid4()
    
    # Generate a UUIDv5 using the custom namespace and the record-specific UUIDv4 as the name
    uuid_obj = uuid.uuid5(NAMESPACE, f"{name}:{record_uuid}")
    
    # Encode the UUIDv5 as Base58
    return base58.b58encode(uuid_obj.bytes).decode('ascii')

def update_csvs(file_model_pairs):
    # Dictionary to store old_id to new_id mappings for each model
    id_mappings = defaultdict(dict)

    # First pass: Generate new IDs
    for file_path, model_name in file_model_pairs:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                old_id = row['id']
                new_id = generate_base58_uuidv5(f"{model_name}:{old_id}")
                id_mappings[model_name][old_id] = new_id

    # Second pass: Update CSVs with new IDs and update foreign keys
    for file_path, model_name in file_model_pairs:
        temp_file_path = file_path + '.temp'
        with open(file_path, 'r') as input_file, open(temp_file_path, 'w', newline='') as output_file:
            reader = csv.DictReader(input_file)
            fieldnames = reader.fieldnames

            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                # Update the primary key
                row['id'] = id_mappings[model_name][row['id']]

                # Update foreign keys and parent_id
                for field in fieldnames:
                    if field.endswith('_id') and field != 'id':
                        related_model = get_related_model(model_name, field)
                        if related_model and row[field] and row[field] in id_mappings.get(related_model, {}):
                            row[field] = id_mappings[related_model][row[field]]
                    elif field == 'parent_id':
                        if row[field] and row[field] in id_mappings[model_name]:
                            row[field] = id_mappings[model_name][row[field]]

                writer.writerow(row)

        # Replace the original file with the updated one
        os.replace(temp_file_path, file_path)
        print(f"Updated {file_path}")

def get_related_model(model_name, field_name):
    # This function should return the related model name based on the current model and field
    # You may need to customize this based on your specific model relationships
    app, model = model_name.split('.')
    
    # Remove '_id' from the field name
    base_field = field_name[:-3] if field_name.endswith('_id') else field_name
    
    # Handle special cases or common patterns
    if base_field == 'user':
        return 'security.User'
    elif base_field == 'person':
        return 'talent.Person'
    elif base_field == 'organisation':
        return 'commerce.Organisation'
    elif base_field == 'product':
        return 'product_management.Product'
    elif base_field == 'skill':
        return 'talent.Skill'
    elif base_field == 'bounty':
        return 'product_management.Bounty'
    elif base_field == 'parent':
        return model_name  # For self-referential relationships
    
    # For other cases, assume the related model is in the same app
    return f"{app}.{base_field.capitalize()}"

# List of (file_path, model_name) pairs
file_model_pairs = [
    ('apps/security/fixtures/user-fixture.csv', 'security.User'),
    ('apps/talent/fixtures/person-fixture.csv', 'talent.Person'),
    ('apps/talent/fixtures/skill-fixture.csv', 'talent.Skill'),
    ('apps/talent/fixtures/expertise-fixture.csv', 'talent.Expertise'),
    ('apps/talent/fixtures/person-skill-fixture.csv', 'talent.PersonSkill'),
    ('apps/commerce/fixtures/organisation-fixture.csv', 'commerce.Organisation'),
    ('apps/product_management/fixtures/product-fixture.csv', 'product_management.Product'),
    ('apps/product_management/fixtures/product-tree-fixture.csv', 'product_management.ProductTree'),
    ('apps/product_management/fixtures/product-area-fixture.csv', 'product_management.ProductArea'),
    ('apps/commerce/fixtures/organisation-point-account-fixture.csv', 'commerce.OrganisationPointAccount'),
    ('apps/commerce/fixtures/product-point-account-fixture.csv', 'commerce.ProductPointAccount'),
    ('apps/commerce/fixtures/platform-fee-configuration-fixture.csv', 'commerce.PlatformFeeConfiguration'),
    ('apps/product_management/fixtures/initiative-fixture.csv', 'product_management.Initiative'),
    ('apps/product_management/fixtures/challenge-fixture.csv', 'product_management.Challenge'),
    ('apps/product_management/fixtures/competition-fixture.csv', 'product_management.Competition'),
    ('apps/product_management/fixtures/bounty-fixture.csv', 'product_management.Bounty'),
    ('apps/talent/fixtures/bounty-bid-fixture.csv', 'talent.BountyBid'),
    ('apps/talent/fixtures/bounty-claim-fixture.csv', 'talent.BountyClaim'),
    ('apps/talent/fixtures/bounty-delivery-attempt-fixture.csv', 'talent.BountyDeliveryAttempt'),
    ('apps/commerce/fixtures/cart-fixture.csv', 'commerce.Cart'),
    ('apps/commerce/fixtures/cart-line-item-fixture.csv', 'commerce.CartLineItem'),
    ('apps/commerce/fixtures/platform-fee-cart-item-fixture.csv', 'commerce.PlatformFeeCartItem'),
    ('apps/commerce/fixtures/sales-tax-cart-item-fixture.csv', 'commerce.SalesTaxCartItem'),
    ('apps/commerce/fixtures/sales-order-fixture.csv', 'commerce.SalesOrder'),
    ('apps/commerce/fixtures/sales-order-line-item-fixture.csv', 'commerce.SalesOrderLineItem'),
    ('apps/commerce/fixtures/point-transaction-fixture.csv', 'commerce.PointTransaction'),
    ('apps/commerce/fixtures/point-order-fixture.csv', 'commerce.PointOrder'),
    ('apps/product_management/fixtures/competition-entry-fixture.csv', 'product_management.CompetitionEntry'),
    ('apps/product_management/fixtures/competition-entry-rating-fixture.csv', 'product_management.CompetitionEntryRating'),
    ('apps/product_management/fixtures/contributor-guide-fixture.csv', 'product_management.ContributorGuide'),
    ('apps/product_management/fixtures/file-attachment-fixture.csv', 'product_management.FileAttachment'),
    ('apps/product_management/fixtures/idea-fixture.csv', 'product_management.Idea'),
    ('apps/product_management/fixtures/idea-vote-fixture.csv', 'product_management.IdeaVote'),
    ('apps/product_management/fixtures/product-contributor-agreement-template-fixture.csv', 'product_management.ProductContributorAgreementTemplate'),
    ('apps/product_management/fixtures/product-contributor-agreement-fixture.csv', 'product_management.ProductContributorAgreement'),
    ('apps/product_management/fixtures/bug-fixture.csv', 'product_management.Bug'),
    ('apps/commerce/fixtures/organisation-point-grant-fixture.csv', 'commerce.OrganisationPointGrant'),
    ('apps/security/fixtures/organisation-person-role-assignment-fixture.csv', 'security.OrganisationPersonRoleAssignment'),
    ('apps/security/fixtures/product-role-assignment-fixture.csv', 'security.ProductRoleAssignment'),
    ('apps/security/fixtures/sign-in-attempt-fixture.csv', 'security.SignInAttempt'),
    ('apps/security/fixtures/sign-up-request-fixture.csv', 'security.SignUpRequest'),
    ('apps/engagement/fixtures/email-notification-fixture.csv', 'engagement.EmailNotification'),
]

if __name__ == '__main__':
    update_csvs(file_model_pairs)
    print("All CSV files have been updated with Base58-encoded UUIDv5 keys, including foreign keys and parent_ids.")