"""
Indivo Admin views
"""

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect 
from django.template.loader import get_template
from admin.forms import FullUserForm, FullUserChangeForm, RecordForm, AccountForm
from admin.lib.indivo import IndivoRecord, IndivoAccount, IndivoContact
from admin.lib.utils import render_admin_response, get_users_to_manage, append_error_to_form
import copy

@login_required()
def admin_show(request):
    return render_admin_response(request, 'home.html') 

@login_required() 
def admin_record_show(request, record_id):
    record = IndivoRecord(record_id=record_id)

    # update recently viewed records
    recents = request.session.get('recent_records', set())
    recents.add(record)
    request.session['recent_records'] = recents

    # populate form from contact document  TODO: currently only handles single phone number
    contact = record.contact
    if contact:
        phone_number = contact.phone_numbers[0] if len(contact.phone_numbers) > 0 else ''
        recordForm = RecordForm(initial={'full_name':contact.full_name or record.label,
                                         'email':contact.email,
                                         'street_address':contact.street_address,
                                         'postal_code':contact.postal_code,
                                         'country':contact.country,
                                         'phone_number':phone_number})
    else:
        recordForm = RecordForm(initial={'full_name':record.label})
        
    return render_admin_response(request, 'record_show.html', {
        'record_form': recordForm,
        'account_form': AccountForm(),
        'record': record
    }) 

@login_required()    
def admin_record_form(request):
    recordForm = RecordForm()
    return render_admin_response(request, 'record_show.html', {
        'record_form': recordForm,
    }) 

@login_required()
def admin_record_create(request):
    form = RecordForm(request.POST) 
    if form.is_valid(): 
        # Process the data in form.cleaned_data
        contact_data = copy.copy(form.cleaned_data)
        contact_data['phone_numbers'] = [contact_data['phone_number']]
        del contact_data['phone_number']
        contact_obj = IndivoContact(contact_data)

        try:
            default_account = IndivoAccount.DEFAULT()
            record = IndivoRecord.from_contact(contact_obj)
            record.push()
            record.set_owner(default_account)
        except Exception as e:
            # TODO
            raise
        return redirect('/admin/record/' + record.record_id + '/')
    else:
        return render_admin_response(request, 'record_show.html', {
            'record_form': form,
        })  

@login_required()    
def admin_record_search(request):
    search_string = request.GET['search_string']
    records = IndivoRecord.search(search_string)

    if (len(records) == 1):
        return redirect('/admin/record/' + records[0].record_id + '/')
    else:
        return render_admin_response(request, 'record_list.html',{
            'records': records,
        })

@login_required()
def admin_record_share_form(request, record_id):
    record = IndivoRecord(record_id=record_id)
    return render_admin_response(request, 'share_add.html', {
        'account_form': AccountForm(),
        'account_search_form': AccountForm(),
        'record': record,
    })
    
@login_required()
def admin_record_share_add(request, record_id):
    record = IndivoRecord(record_id=record_id)

    if request.POST['existing'] == 'False':
        # Create new Account and add Share
        form = AccountForm(request.POST)
        if form.is_valid(): 
            # TODO: generate account id
            account = IndivoAccount(account_id=form.cleaned_data['email'], 
                                    full_name=form.cleaned_data['full_name'], 
                                    contact_email=form.cleaned_data['email'])
            try:
                account.push()
            except ValueError as e:
                append_error_to_form(form, 'email', str(e))
                return render_admin_response(request, 'share_add.html', {
                        'account_form': form,
                        'account_search_form': AccountForm(),
                        'record': record,
                        })

            record.create_fullshare_with(account)
            return redirect('/admin/record/' + record_id +'/')
        else:
            return render_admin_response(request, 'share_add.html', {
                'account_form': form,
                'account_search_form': AccountForm(),
                'record': record,
            })
    else:
        # Add share to existing Account
        try:
            accounts = IndivoAccount.search(full_name=request.POST['full_name'],
                                            contact_email=request.POST['email'])
            
        except Exception as e:
            #TODO
            raise e
        return render_admin_response(request, 'share_add.html', {
                'record': record,
                'accounts': accounts,
                'account_search_form': AccountForm(initial={'full_name':request.POST['full_name'], 
                                                            'email':request.POST['email']})
            })

@login_required()
def admin_record_account_share_delete(request, record_id, account_id):
    record = IndivoRecord(record_id=record_id)
    account = IndivoAccount(account_id=account_id, new=False)
    success = record.remove_fullshare_with(account)
    if not success:
        # TODO
        raise Exception("couldn't delete share!")
    
    return redirect('/admin/record/' + record_id + '/')

@login_required()
def admin_record_account_share_add(request, record_id, account_id):
    record = IndivoRecord(record_id=record_id)
    account = IndivoAccount(account_id=account_id, new=False)
    try:
        share = record.create_fullshare_with(account)
    except Exception as e:
        # TODO
        raise
    return redirect('/admin/record/' + record_id +'/')

@login_required()
def admin_record_owner_form(request, record_id):
    return render_admin_response(request, 'owner_set.html', {
        'account_form': AccountForm(),
        'account_search_form': AccountForm(),
        'record': IndivoRecord(record_id=record_id),
    })

@login_required()
def admin_record_owner(request, record_id):
    record = IndivoRecord(record_id = record_id)
    
    if request.POST['existing'] == 'False':

        # Create new Account and set as Owner
        form = AccountForm(request.POST)
        if form.is_valid(): 

            # TODO: generate account id
            account = IndivoAccount(account_id=form.cleaned_data['email'], 
                                    full_name=form.cleaned_data['full_name'], 
                                    contact_email=form.cleaned_data['email'])
            try:
                account.push()
            except ValueError as e:
                append_error_to_form(form, 'email', str(e))
                return render_admin_response(request, 'share_add.html', {
                        'account_form': form,
                        'account_search_form': AccountForm(),
                        'record': record,
                        })

            account = record.set_owner(account)            
            return redirect('/admin/record/' + record_id +'/')
        else:
            return render_admin_response(request, 'owner_set.html', {
                'account_form': form,
                'account_search_form': AccountForm(),
                'record': record
            })
    else:
        # set existing Account as owner
        account = []
        try:
            accounts = IndivoAccount.search(full_name=request.POST['full_name'], 
                                            contact_email=request.POST['email'])
        except Exception as e:
            #TODO
            raise e
        return render_admin_response(request, 'owner_set.html', {
                'record': record,
                'accounts': accounts,
                'account_search_form': AccountForm(initial={'full_name':request.POST['full_name'], 
                                                            'email':request.POST['email']})
            })

@login_required()
def admin_record_account_owner_set(request, record_id, account_id):
    record = IndivoRecord(record_id=record_id)
    account = IndivoAccount(account_id=account_id, new=False)
    try:
        record.set_owner(account)
    except Exception as e:
        # TODO
        raise
    return redirect('/admin/record/' + record_id +'/')

@login_required()    
def admin_account_show(request, account_id):
    account = IndivoAccount(account_id=account_id, new=False)
    return render_admin_response(request, 'account.html', {
        'account': account
    }) 

@login_required()
def admin_account_retire(request, account_id):
    account = IndivoAccount(account_id=account_id, new=False)
    account.retire()
    return redirect('/admin/account/' + account_id + '/')

@login_required()
@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_users_show(request):
    return render_admin_response(request, 
                                       'user_list.html', 
                                       {'users':get_users_to_manage(request),
                                        'user_form':FullUserForm(),})

@login_required()
@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_user_create(request):
    form = FullUserForm(request.POST) 
    try:
        form.save()
        return redirect('/admin/users/')
    except ValueError:
        return render_admin_response(request, 
                                           'user_list.html', 
                                           {'users':get_users_to_manage(request),
                                            'user_form':form,})
    except Exception as e:
        # TODO
        raise

@login_required()
@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_user_edit(request, user_id):
    if request.method == "GET":
        try:
            user = User.objects.get(id=user_id)
            return render_admin_response(request, 'user_edit.html',
                                               {'u':user,
                                                'user_form':FullUserChangeForm(instance=user),})
        except User.DoesNotExist:
            # TODO
            raise
        except Exception as e:
            # TODO
            raise
    else:
        try:
            user = User.objects.get(id=user_id)
            form = FullUserChangeForm(request.POST, instance=user)
            form.save()
            return redirect('/admin/users/')
        except ValueError:
            return render_admin_response(request, 'user_edit.html',
                                               {'u':user,
                                                'user_form':form,})
        except User.DoesNotExist:
            # TODO
            raise
        except Exception as e:
            # TODO
            raise

@login_required()
@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_user_deactivate(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = False
        user.save()
        return redirect('/admin/users/')
    except User.DoesNotExist:
        # TODO
        raise
    except Exception as e:
        # TODO
        raise

@login_required()
@user_passes_test(lambda u: u.is_superuser, login_url='/admin/')
def admin_user_activate(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()
        return redirect('/admin/users/')
    except User.DoesNotExist:
        # TODO
        raise
    except Exception as e:
        # TODO
        raise
