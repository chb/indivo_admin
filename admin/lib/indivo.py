"""
Utils for the Admin interface.

"""

from django.conf import settings
from lxml import etree
from django.template.loader import get_template
from django.template import Context
from indivo_client_py.lib.client import IndivoClient

DOC_NS = 'http://indivo.org/vocab/xml/documents#'

class IndivoManager(object):
    def __init__(self):
        self.client = self.get_indivo_client()
        self.default_account_id = None

    def get_indivo_client(self):
        key, secret = settings.INDIVO_OAUTH_CREDENTIALS
        client = IndivoClient(key, secret, settings.INDIVO_SERVER_LOCATION)
        return client

    def make_api_call(self, client_func_name, *args, **kwargs):
        client_func = getattr(self.client, client_func_name, None)
        if not client_func:
            raise ValueError('Invalid API Call: %s'%(client_func_name))
        
        resp = client_func(*args, **kwargs)
        try:
            resp = resp.response
        except AttributeError:
            pass

        response_code = resp['response_status']

        try:
            response_data = resp['response_data']
        except KeyError:
            try:
                response_data = resp['prd']
            except KeyError:
                response_data = ''
        
        # if the response was XML, return an etree
        try:
            response_data = etree.XML(response_data)
        except Exception, e:
            pass

        return (response_code, response_data)

class IndivoModel(object):
    manager = IndivoManager()
    primary_key = None

    def __eq__(self, other):
        my_pk_field = getattr(self, 'primary_key', None)
        other_pk_field = getattr(other, 'primary_key', None)

        if my_pk_field != other_pk_field:
            return False
        
        if my_pk_field:
            my_primary_key = getattr(self, my_pk_field, None)
            other_primary_key = getattr(other, my_pk_field, None)
            if my_primary_key or other_primary_key:
                return my_primary_key == other_primary_key
        
        return id(self) == id(other)
 
    def __hash__(self):
        return hash(getattr(self, 'primary_key'))

class IndivoRecord(IndivoModel):
    """ Represent an Indivo Record. """
    
    primary_key = 'record_id'

    @classmethod
    def from_etree(cls, xml_etree):
        record = cls()
        record.record_id = xml_etree.get('id')
        record.label = xml_etree.get('label')
        return record

    @classmethod
    def from_contact(cls, contact_obj):
        return cls(contact_obj=contact_obj, label=contact_obj.full_name)

    @classmethod
    def search(cls, search_string):
        matches = []
        status, data = cls.manager.make_api_call('record_search', parameters={'label':search_string})
        if status == 200:
            for record in data.findall('Record'):
                matches.append(cls.from_etree(record))
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

        return matches

    def __init__(self, record_id=None, label=None, contact_obj=None):
        self.record_id = record_id
        self.label = label
        self.contact = contact_obj
        self.owner = None
        self.fullshares = {}
        self.carenetshares = []

        if self.record_id:
            self._fetch()

    def push(self):
        if self.record_id:
            # TODO: implement update
            raise ValueError("Record already created.")
        elif not self.contact:
            raise ValueError("No contact data to create record with")
        else:
            self.record_id = self._create_on_server()

    def set_owner(self, account):
        status, data = self.manager.make_api_call('set_record_owner', 
                                                  record_id=self.record_id, 
                                                  data=account.account_id)
        if status == 200:
            return True
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def create_fullshare_with(self, account):
        data = {'account_id': account.account_id} # Add role label?
        status, data = self.manager.make_api_call('create_share', 
                                                  record_id=self.record_id, 
                                                  data=data)
        if status == 200:
            self.fullshares[account.account_id] = account
            return True
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def remove_fullshare_with(self, account):
        status, data = self.manager.make_api_call('delete_share',
                                                  record_id=self.record_id, 
                                                  account_id=account.account_id)
        if status == 200:
            if self.fullshares.has_key(account.account_id):
                del self.fullshares[account.account_id]
            return True
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _fetch(self):
        if self.record_id:
            self.contact = self._get_contact()
            self.label = self.contact.full_name or self._get_label()
            self.owner = self._get_owner()
            self.fullshares = self._get_fullshares()
            self.carenetshares = self._get_carenetshares()

    def _get_label(self):
        status, data = self.manager.make_api_call('read_record',
                                                  record_id=self.record_id)
        if status == 200:
            return data.get('label')
        else:
            #TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _get_fullshares(self):
        status, data = self.manager.make_api_call('get_shares',
                                                  record_id=self.record_id)
        if status == 200:
            shares = {}
            for share in data.findall('Share'):
                account_id = share.get('account', None)
                if account_id:
                    shares[account_id] = IndivoAccount(account_id=account_id, new=False)
            return shares
        else:
            #TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _get_carenetshares(self):
        status, data = self.manager.make_api_call('get_record_carenets', 
                                                  record_id=self.record_id)
        if status == 200:
            carenet_names = dict([(c.get('id'), c.get('name')) for c in data.findall('Carenet')])
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

        carenet_accounts = {}
        for c_id in carenet_names.keys():
            status, data = self.manager.make_api_call('get_carenet_accounts',
                                                      carenet_id=c_id)
            if status == 200:
                for account in data.findall('CarenetAccount'):
                    account_carenets = carenet_accounts.setdefault(account.get('id'), [])
                    account_carenets.append(carenet_names[c_id])
            else:
                # TODO
                raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

        ret = []
        for email, carenets in carenet_accounts.items():
            account_obj = IndivoAccount(account_id=email, new=False)
            account_obj.full_name += (" (%s)"%", ".join(carenets))
            ret.append(account_obj)
        return ret

    def _get_owner(self):
        status, data = self.manager.make_api_call('get_record_owner',
                                                  record_id=self.record_id)
        if status == 200:
            account_id = data.get('id')
            return IndivoAccount(account_id=account_id, new=False)
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _get_contact(self):
        status, data = self.manager.make_api_call('read_special_document', 
                                                  record_id=self.record_id,
                                                  special_document='contact')
        if status == 200:
            return IndivoContact.from_etree(data)
        
        # contact wasn't found, return an empty contact
        elif status == 404:
            return IndivoContact()
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _create_on_server(self):
        status, data = self.manager.make_api_call('create_record', data=self.contact.to_xml())
        if status == 200:
            record_id = data.get('id')
            return record_id
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))
    
class IndivoAccount(IndivoModel):
    """ Represent and Indivo Account. """

    primary_key = 'account_id'

    @classmethod
    def from_etree(cls, xml_etree, new=False):
        account = cls(new=new)
        account._update_from_etree(xml_etree)
        return account

    @classmethod
    def DEFAULT(cls):

        # try fetching the account
        default_info = settings.DEFAULT_ADMIN_OWNER
        account = cls(account_id=default_info['email'], 
                      full_name=default_info['full_name'],
                      contact_email=default_info['contact_email'], new=False)

        try:
            account._fetch()
        except ValueError as e:
            
            # account didn't exist: create it
            account.push()

        return account

    @classmethod
    def search(cls, full_name=None, contact_email=None):
        if not full_name and not contact_email:
            return []
        else:
            req_data = {'fullname':full_name, 'contact_email':contact_email}
            status, data = cls.manager.make_api_call('account_search', parameters=req_data)
            if status == 200:
                return [cls.from_etree(a) for a in data.findall('Account')]
            else:
                # TODO
                raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def __init__(self, account_id=None, full_name=None, contact_email=None, new=True):
        self.account_id = account_id
        self.full_name = full_name
        self.contact_email = contact_email
        self.state = None
        self.secondary_secret = None
        self.fullshares = {}

        if not new:
            self._fetch()

    @property
    def secondary_secret_pretty(self):
        if self.secondary_secret:
            return self.secondary_secret[:3] + '-' + self.secondary_secret[-3:]
        return ''

    def push(self):
        acct_etree = self._create_on_server()
        if acct_etree:
            self._update_from_etree(acct_etree)

    def retire(self):
        data = {'state':'retired'}
        status, data = self.manager.make_api_call('account_set_state', 
                                                  account_id=self.account_id, 
                                                  data=data)
        if status == 200:
            self.state = 'retired'
            return True
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _fetch(self):
        if self.account_id:
            self._get_account_info()
            self._get_fullshares()

    def _get_fullshares(self):
        status, data = self.manager.make_api_call('get_account_records',
                                                  account_id=self.account_id)
        if status == 200:
            carenetmap = {}
            carenetshared = set([])
            fullshared = []
            owned = []
            for record in data.findall('Record'):
                record_obj = IndivoRecord.from_etree(record)
                shared = record.get('shared', None)
                if not shared:
                    owned.append(record_obj)
                elif record.get('carenet_name'):
                    carenet_name = record.get('carenet_name')
                    carenets = carenetmap.setdefault(record_obj.record_id, [])
                    carenets.append(carenet_name)
                    record_obj.label = record_obj.label.replace('(carenet)', '').strip() 
                    carenetshared.add(record_obj)
                else:
                    record_obj.label = record_obj.label.replace('(shared)', '').strip()
                    fullshared.append(record_obj)
            self.fullshared_records = fullshared
            self.owned_records = owned
            
            # add a helpful label to carenet records
            for r in carenetshared:
                label_suffix = ' (%s)' % ", ".join(carenetmap[r.record_id])
                r.label += label_suffix
            self.carenet_records = carenetshared
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))
 
    def _get_account_info(self):
        status, data = self.manager.make_api_call('account_info', account_id=self.account_id)
        if status == 200:
            self._update_from_etree(data)
            return True
        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

    def _update_from_etree(self, xml_etree):
        self.account_id = xml_etree.get('id')
        self.secondary_secret = xml_etree.findtext('secret')
        self.full_name = xml_etree.findtext('fullName')
        self.contact_email = xml_etree.findtext('contactEmail')
        self.state = xml_etree.findtext('state')
            
    def _create_on_server(self):
        data = {
            'account_id':self.account_id,
            'primary_secret_p':'1',
            'secondary_secret_p':'1',
            'contact_email':self.contact_email,
            'full_name':self.full_name,
            }
        status, data = self.manager.make_api_call('create_account', data)
        if status == 200:
            return data

        # account_id already taken
        elif status == 400:
            # TODO
            raise ValueError(data)

        else:
            # TODO
            raise ValueError("Bad response from Indivo: [%s] %s"%(status, data))

class IndivoContact(object):
    """ Represent an Indivo Contact Document.

    XML Looks like:

    <Contact xmlns="http://indivo.org/vocab/xml/documents#">
      <name>
        <fullName>Sebastian Rockwell Cotour</fullName>
        <givenName>Sebastian</givenName>
        <familyName>Cotour</familyName>
      </name>
      <email type="personal">
        <emailAddress>scotour@hotmail.com</emailAddress>
      </email>
      <email type="work">
        <emailAddress>sebastian.cotour@childrens.harvard.edu</emailAddress>
      </email>
      <address type="home">
        <streetAddress>15 Waterhill Ct.</streetAddress>
        <postalCode>53326</postalCode>
        <locality>New Brinswick</locality>
        <region>Montana</region>
        <country>US</country>
        <timeZone>-7GMT</timeZone>
      </address>
      <location type="home">
        <latitude>47N</latitude>
        <longitude>110W</longitude>
      </location>
      <phoneNumber type="home">5212532532</phoneNumber>
      <phoneNumber type="work">6217233734</phoneNumber>
      <instantMessengerName protocol="aim">scotour</instantMessengerName>
    </Contact>

    """
    
    ns = DOC_NS
    
    def __init__(self, data={}):
        self.full_name = None
        self.given_name = None
        self.family_name = None
        self.email = None
        self.street_address = None
        self.region = None
        self.postal_code = None
        self.country = None
        self.phone_numbers = []

        for attr, val in data.iteritems():
            try:
                setattr(self, attr, val)
            except Exception:
                pass
    
    def to_xml(self):
        return get_template("contact.xml").render(Context({'contact':self}))

    @classmethod
    def find_text_anywhere(cls, xml_etree, tagname):
        full_tag = './/{%s}%s'%(cls.ns, tagname)
        return xml_etree.findtext(full_tag)

    @classmethod
    def findalltext(cls, xml_etree, text):
        return [el.text for el in xml_etree.iterfind(text)]

    @classmethod
    def from_xml(cls, xml_str):
        xml_etree = etree.XML(xml_str)
        return cls.from_etree(xml_etree)
        
    @classmethod
    def from_etree(cls, xml_etree):
        contact = cls()
        contact.full_name = cls.find_text_anywhere(xml_etree, 'fullName')
        contact.given_name = cls.find_text_anywhere(xml_etree, 'givenName')
        contact.family_name = cls.find_text_anywhere(xml_etree, 'familyName')
        contact.email = cls.find_text_anywhere(xml_etree, 'emailAddress')
        contact.street_address  = cls.find_text_anywhere(xml_etree, 'streetAddress')
        contact.region = cls.find_text_anywhere(xml_etree, 'region')
        contact.postal_code = cls.find_text_anywhere(xml_etree, 'postalCode')
        contact.country = cls.find_text_anywhere(xml_etree, 'country')
        contact.phone_numbers = cls.findalltext(xml_etree, '{%s}phoneNumber'%cls.ns)
        return contact
