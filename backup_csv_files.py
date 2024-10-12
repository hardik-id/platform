import os
import shutil
import datetime

def backup_csv_files(file_model_pairs):
    # Create a backup directory with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"csv_backup_{timestamp}"
    os.mkdir(backup_dir)

    # Copy each CSV file to the backup directory
    for file_path, _ in file_model_pairs:
        if os.path.exists(file_path):
            # Create the directory structure in the backup folder
            backup_file_path = os.path.join(backup_dir, file_path)
            os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
            
            # Copy the file
            shutil.copy2(file_path, backup_file_path)
            print(f"Backed up: {file_path}")
        else:
            print(f"Warning: {file_path} does not exist. Skipping.")

    print(f"Backup completed. Files saved in '{backup_dir}' directory.")

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
    backup_csv_files(file_model_pairs)