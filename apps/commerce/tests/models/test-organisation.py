import pytest
from django.core.exceptions import ValidationError
from apps.commerce.models import Organisation

@pytest.mark.django_db
class TestOrganisation:
    def test_create_organisation(self, organisation):
        assert organisation.name == 'Test Org'
        assert organisation.country == 'US'
        assert organisation.tax_id == '123456789'

    def test_invalid_tax_id(self):
        with pytest.raises(ValidationError):
            Organisation.objects.create(name='Invalid Org', country='US', tax_id='123')

    def test_valid_us_ein(self):
        org = Organisation.objects.create(name='US Org', country='US', tax_id='123456789')
        assert org.is_valid_us_ein()

    def test_valid_vat_number(self):
        org = Organisation.objects.create(name='UK Org', country='GB', tax_id='GB123456789')
        assert org.is_valid_vat_number()

    def test_get_tax_id_display(self):
        us_org = Organisation.objects.create(name='US Org', country='US', tax_id='123456789')
        uk_org = Organisation.objects.create(name='UK Org', country='GB', tax_id='GB123456789')
        assert us_org.get_tax_id_display() == 'EIN: 123456789'
        assert uk_org.get_tax_id_display() == 'VAT: GB123456789'

    def test_str_representation(self, organisation):
        assert str(organisation) == 'Test Org'
