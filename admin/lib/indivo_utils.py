"""
Utils for the Admin interface.

"""

from django.core.exceptions import *

def create_indivo_record(contact_xml, creator):
    """" 
    Create a record, then log that to the admin logs.
    """
    # TODO

def create_indivo_account(creator, account_id, full_name='', contact_email=None):
    account = _account_create(creator, account_id=account_id, full_name=full_name,
                              contact_email=contact_email, secondary_secret_p="1")
    return account

def create_indivo_fullshare(record, account):
    RecordNotificationRoute.objects.get_or_create(record=record, account=account)
    share, created_p = AccountFullShare.objects.get_or_create(record=record, with_account=account, 
                                                              role_label='Guardian')
    return share

def remove_indivo_fullshare(record, account):
    try:
        AccountFullShare.objects.get(record=record, with_account=account).delete()
    except AccountFullShare.DoesNotExist:
        return False

    return True

def set_indivo_record_owner(record, account):
    record.owner = account
    record.save()

    return account

def retire_indivo_account(account):
    account.set_state('retired')
    account.save()
    return account
