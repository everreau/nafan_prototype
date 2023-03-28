from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from .managers import UserManager

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from bs4 import BeautifulSoup
from pymarc import MARCReader
from PyPDF2 import PdfFileReader
from sickle import Sickle

import json, re

class UserRole(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)

    CONTRIBUTOR = "CO"
    REPO_ADMIN = "RA"
    USER_ROLES = [(CONTRIBUTOR, 'Contributor'),
                  (REPO_ADMIN, 'Repository Admin'),]
    role = models.CharField(max_length=2,
                            choices=USER_ROLES,
                            default=CONTRIBUTOR,)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff'), default=False)
    is_site_admin = models.BooleanField(_('site admin'), default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        '''
        Returns the first_name plus the last_name, with a space in between.
        '''
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        '''
        Returns the short name for the user.
        '''
        return self.first_name

    def get_user_repositories(self):
        if self.is_site_admin:
            return Repository.objects.all()
        else:
            return Repository.objects.filter(pk__in=self.userrole_set.all().values_list('repository__pk', flat=True))
        
    def is_repo_admin(self, repo):
        return self.is_site_admin or UserRole.objects.filter(repository=repo, user=self, role=UserRole.REPO_ADMIN).exists()

    def is_repo_member(self, repo):
        return self.is_site_admin or UserRole.objects.filter(repository=repo, user=self).exists()
    
    def is_admin(self):
        return self.is_site_admin or UserRole.objects.filter(user=self, role=UserRole.REPO_ADMIN).exists()
    
    def user_type(self):
        if self.is_site_admin:
            return "Site Admin"
        elif UserRole.objects.file(role=UserRole.REPO_ADMIN).exists():
            return "Repository Admin"
        elif UserRole.objects.file(role=UserRole.CONTRIBUTOR).exists():
            return "Contributor"
        else:
            return "Unassigned"

    def __str__(self):
        return self.get_full_name()

class RepositoryType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Repository(models.Model):
    name = models.CharField(verbose_name="Repository", max_length=255, blank=False)
    slug = models.SlugField(max_length=50)
    UNKNOWN = "UN"
    UNVERIFIED = "UV"
    PUBLIC = "PU"
    STATUSES = [(UNKNOWN, 'Unknown'),
                (UNVERIFIED, 'Unverified'),
                (PUBLIC, 'Public'),]
    status = models.CharField(max_length=2,
                             choices=STATUSES,
                            default=UNKNOWN,)
    
    repository_type = models.ForeignKey('RepositoryType',  on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)
    
    street_address_1 = models.CharField(max_length=255, blank=True)
    street_address_2 = models.CharField(max_length=255, blank=True)
    po_box = models.CharField(max_length=255, blank=True)
    st_city = models.CharField(verbose_name="City", max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    st_zip_code_5_numbers = models.CharField(max_length=255, blank=True)
    st_zip_code_4_following_numbers = models.CharField(max_length=255, blank=True)
    street_address_county = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=32, blank=True)

    url = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)

    latitude = models.CharField(max_length=255, blank=True)
    longitude = models.CharField(max_length=255, blank=True)

    notes = models.TextField(blank=True)
    governing_access = models.TextField(blank=True)

    elasticsearch_id = models.CharField(max_length=32, blank=True)

    def get_defaults(self):
        return FindingAidDefaults.objects.get(repository=self)

    def get_absolute_url(self):
        return reverse('detail-repository', kwargs={'slug' : self.slug})

    def __str__(self):
        return self.name

class JoinRequest(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=25)
    url = models.URLField(max_length=255,blank=True)
    message = models.TextField()

    def __str__(self):
        return self.full_name
    
class FindingAidDefaults(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)
    governing_access = models.TextField(blank=True)
    rights = models.TextField(blank=True)
    creative_commons = models.URLField(max_length=255)

    def __str__(self):
        return f'{self.repository} defaults'

class HarvestProfile(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    location = models.URLField(max_length=255)

    FILE = 'F'
    DIR = 'D'
    SITEMAP = 'S'
    OAI = 'O'
    HARVEST_TYPES = [(FILE, 'File'),(DIR, 'Directory'), (SITEMAP, 'Sitemap'), (OAI, 'OAI-PMH')]
    harvest_type = models.CharField(max_length=1, choices=HARVEST_TYPES, default=FILE)

    EAD = 'E'
    MARC = 'M'
    PDF = 'P'
    FILE_TYPES = [(EAD, 'EAD'), (MARC, 'MARC (under development)'), (PDF, 'PDF (under development)')]
    default_format = models.CharField(max_length=1, choices=FILE_TYPES, default=EAD)

    def get_harvest_type(self):
        return self.harvest_type #self.HARVEST_TYPES[self.harvest_type]
    
    def get_default_format(self):
        return self.default_format #self.FILE_TYPES[self.default_format]

    def get_absolute_url(self):
        return reverse('detail-profile', kwargs={'slug': self.repository.slug, 'pk' : self.pk})

    def __str__(self):
        return self.name


class FindingAid(models.Model):
    repository = models.ForeignKey('Repository', on_delete=models.CASCADE)
    # active?

    EAD = 'E'
    MARC = 'M'
    PDF = 'P'
    RECORD_TYPES = [(EAD, 'EAD'), (MARC, 'MARC'), (PDF, 'PDF (under development)')]
    record_type = models.CharField(max_length=1, choices=RECORD_TYPES, default=EAD)
    elasticsearch_id = models.CharField(max_length=32, blank=True)
    last_update = models.DateTimeField(blank=True)
    updated_by = models.ForeignKey('User', blank=True, null=True, on_delete=models.SET_NULL)
    revision_notes = models.TextField(blank=True)

    # Basic finding structure corresponding to DACS several fields overlap with EAD
    # should be repeating
    reference_code = models.TextField(blank=True)

    title = models.TextField(blank=False)
    date = models.TextField(blank=True)
    extent = models.TextField(blank=True)
    creator = models.TextField(blank=True)
    scope_and_content = models.TextField(blank=True)
    governing_access = models.TextField(blank=True)
    languages = models.TextField(blank=True)
    rights = models.TextField(blank=True)
    indent = models.TextField(blank=True)

    intra_repository = models.TextField(blank=True)
    level = models.CharField(max_length=32, blank=True)
    creative_commons = models.CharField(max_length=32, blank=True)

    custodhist = models.TextField(blank=True)
    acqinfo = models.TextField(blank=True)
    processinfo = models.TextField(blank=True)
    container = models.TextField(blank=True)

    repository_link = models.TextField(blank=True)
    digital_link = models.TextField(blank=True)
    
    scope_and_content_raw = models.TextField(blank=True)
    note = models.TextField( blank=True)

    abstract = models.TextField(blank=True)
    citation = models.TextField(blank=True)
    bioghist = models.TextField(blank=True)
    originals_location = models.TextField(blank=True)
    
    ark = models.TextField(blank=True)
    snac = models.TextField(blank=True)
    wiki = models.TextField(blank=True)
    associated_file = models.FileField(upload_to='uploads/', blank=True)

    # archref needs to be treated like a <cXX> element
    # bibliography consists of a list of <bibref> and/or other elements, pull into single entry
    # <c> treated with a find_all and handled like the <cXX>
    
    # This is the base Finding aid ID used to maintain relationships between the archref and <cXX>
    # components within the search engine as each are independent entries
    progenitorID = models.IntegerField(default=0, blank=True)

    # This is used to keep the relationship going through <cXX> components
    parentID = models.IntegerField(default=0, blank=True)

    component = models.CharField(max_length=10, blank=True)

    def get_absolute_url(self):
        return reverse('detail-findingaid', kwargs={'pk' : self.pk, 'slug': self.repository.slug})

    def __str__(self):
        return self.title
    
    def get_contents(self):
        return FindingAid.objects.filter(progenitorID=self.id).order_by('pk')

    def get_chron(self):
        return self.chronology_set.all().order_by('sort_order')
    
    def get_series(self):        
        return FindingAid.objects.filter(progenitorID=self.id,level="c01").order_by('pk')

    def get_names(self):
        return self.controlaccess_set.filter(control_type="persname").order_by('term')
    
    def get_subjects(self):
        return self.controlaccess_set.filter(control_type="subject").order_by('term')
    
    def get_materials(self):
        return self.controlaccess_set.filter(control_type="genreform").order_by('term')

    # The Elasticsearch index consists of:
    # id - finding aid ID
    # type - type of item being indexed (web page, EAD, MARC, etc.)
    # title - title of the item being indexed
    # repository - name of the repository that owns the finding aid
    # content - whatever makes sense to index
    # source - Originally thought to hold things like file name, not sure if it is useful anymore
    # destination - Originally thought to hold the link to external links, not used and always blank currently

    def create_index(id, index_type, title, repository_name, description, source):
        elasticsearch_id = "Fail"   # Bit dicey to mix and match IDs and text, but if Python doesn't care...

        # If there is something to index
        if title or description:
            es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
            
            # For insert no need for {'doc': }
            record = {'id': id, 'type': index_type, 'title': title, 'repository': repository_name, 'content': description, 'source': source, 'destination': ""}
            json_record = json.dumps(record)

            try:
                outcome = es.index(index='nafan', doc_type='_doc', body=json_record)
                elasticsearch_id = outcome['_id']

            except Exception as ex:
                print('Error in indexing data')
                print(str(ex))
        
        return elasticsearch_id

    def update_index(id, elasticsearch_id, index_type, title, repository_name, description, source):
        # If there is something to index
        if title or description:
            
            es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

            # For update it needs to be wrapped in {'doc': }
            record = {'doc':{'id': id, 'type': index_type, 'title': title, 'repository': repository_name, 'content': description, 'source': source, 'destination': ""}}
            json_record = json.dumps(record)

            try:
                outcome = es.update(id=elasticsearch_id, index='nafan', doc_type='_doc', body=json_record)
                elasticsearch_id = outcome['_id']
            except Exception as ex:
                print('Error in indexing data')
                print(str(ex))

        return elasticsearch_id

    def remove_index(elasticsearch_id):
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

        try:
            es.delete(index="nafan",doc_type="_doc", id=elasticsearch_id)
        except Exception as ex:
            print('Error in indexing data')
            print(str(ex))

    def ead_index(id, repository, filepath, user_name):                    
        response = "OK"

        with open(filepath, newline='', encoding="utf8") as ead_file:

            if id == "new":
                f = FindingAid()
            else:
                f = FindingAid.objects.get(id=id)

            f.record_type = "ead"
            f.repository = repository

            # Yank the text and start parsing it
            html_doc = ead_file.read()
            soup = BeautifulSoup(html_doc, 'html.parser')

            # Make an internal EAD from the initial file
            # The EAD parsing is not as elegant as it should be in a final implementation
            response = f.make_ead(id, soup, f, user_name, filepath)

        return response

    def make_ead(id, soup, aid, user_name, filepath):
        
        response = "OK"

        # Access the search engine for indexing
        es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

        try:

            archdesc = soup.find('archdesc')
            did = archdesc.find('did')

            # parse the archdesc did
            aid = FindingAid.parse_did(did, aid, "archdesc")

            # if the following weren't found in the high did, go look for them

            # Have to consider there will be more than one dao
            # The digital object can be specified with an entityref attribute.  Need example.
            digital_link = soup.find_all('dao') 
            # if FindingAid.legit_component(digital_link, component_level):
            for digitals in digital_link:
                aid.digital_link = digitals['href']   

            # There can be multiple accessrestrict entries
            if not aid.governing_access:
                aid.governing_access = String_or_p_tag(soup, 'accessrestrict')
                # governing_access = did.find_all('accessrestrict') 
                # if governing_access:
                #     for entry in governing_access:
                #         aid.governing_access = aid.governing_access + entry.get_text() + " "
                #     aid.governing_access = cleanhtml(str(aid.governing_access))
                #     aid.governing_access = aid.governing_access.strip()

            if not aid.rights:
                aid.rights = String_or_p_tag(soup, 'userestrict')
            
            if not aid.citation:
                aid.citation = String_no_p_tag(soup, 'prefercite')
            
            if not aid.bioghist:
                aid.bioghist = String_or_p_tag(soup, 'bioghist')
            
            if not aid.scope_and_content:
                aid.scope_and_content = String_or_p_tag(soup, 'scopecontent')
            
            if not aid.custodhist:
                aid.custodhist = String_or_p_tag(soup, 'custodhist')
            
            if not aid.acqinfo:
                aid.acqinfo = String_or_p_tag(soup, 'acqinfo')
            
            if not aid.processinfo:
                process = soup.find_all('processinfo')
                if process:
                    for item in process:
                        try:
                            aid.processinfo = aid.processinfo + " " + item.p.string
                        except Exception as ex:
                            print('Error handling processinfo ' + str(ex))

            if not aid.originals_location:
                aid.originals_location = String_or_p_tag(soup, 'originalsloc')
                
            # Mark the indexing date and the user who did the indexing
            today = date.today()
            aid.last_update = today.strftime("%B %d, %Y")
            aid.updated_by = user_name

            aid.save()

            # The progenitor is used to keep track of related archdesc and cXX entries
            progenitorID = aid.pk

            aid.ark = "ark://" + str(aid.pk)

            # If the snac and wiki links are going to be, a method for specifying them
            # needs to be introduced.  Same problem as always with mass uploads
            aid.snac = "https://snaccooperative.org"
            aid.wiki = "https://www.wikidata.org"

            sortOrder = 0
            chronology = soup.find_all('chronitem')
            if chronology:
                for chron in chronology:
                    item = Chronology()
                    item.finding_aid_id = aid.pk
                    item.date = chron.date.string
                    item.event = chron.event.string
                    item.sort_order = sortOrder
                    item.save()
                    sortOrder = sortOrder + 1

                    # after the aid is saved, other aspects of the finding aid can be associated

                    # the language information probably needs to come down here

                    # <controlaccess>
                    # subheaders
                    #   <corpname>
                    #   <famname>
                    #   <function>
                    #   <genreform>
                    #   <geogname>
                    #   <occupation>
                    #   <persname>
                    #   <subject>
                    #   <title>

            control = soup.find('controlaccess')
            if control:
                entries = control.find_all('corpname')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "corpname"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('famname')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "famname"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('function')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "function"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('genreform')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "genreform"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('geogname')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "geogname"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('occupation')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "occupation"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('persname')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "persname"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('subject')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "subject"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()
                entries = control.find_all('title')
                if entries:
                    for entry in entries:
                        item = ControlAccess()
                        item.finding_aid_id = progenitorID
                        item.control_type = "title"
                        item.term = entry.string
                        if entry.has_attr('authfilenumber'):
                            item.link = entry['authfilenumber']
                        item.save()

            # Once the control list is filled, add them to the finding aid through FindingAidSubjectHeader
            # Needs to be implemented
                
            # otherfindaid can be text or an extref link to another finding aid
            # There can be multiple subheaders or combinations thereof
            # has to be handled like <controlaccess>
            temp = ""
            other = soup.find('otherfindaid')
            if other:
                entries = other.find_all('bibref')
                for entry in entries:
                    temp = entry.get_text()
                    temp = cleanhtml(str(temp))

                        # The entry contains all the text of an element with the tags including the searched tag
                        # So theoretically the get_text could be indexed while the entry is stored in the database
                        # to be processed converting the tags to html format (or do it on the way into the database)
                        # print(entry)

                entries = other.find_all('extref')
                for entry in entries:
                    temp = entry.string
                    temp = entry['href']

            # Process the component fields through a recursive function
            components_list = []
            c01s = soup.find_all("c01")
            for c01 in c01s:
                FindingAid.ProcessComponents(soup, c01, progenitorID, progenitorID, 1)

            try:

                # Index the processed portion of the EAD.  Each component is indexed separately.

                source_url = filepath
                destination_url = ""

                if id == "new":

                    record = {'id': aid.pk, 'type': aid.aid_type, 'title': aid.title, 'repository': aid.repository, 'content': aid.scope_and_content, 'source': source_url, 'destination': destination_url}
                    json_record = json.dumps(record)

                    outcome = es.index(index='nafan', doc_type='_doc', body=json_record)
                    elasticsearch_id = outcome['_id']

                    aid.elasticsearch_id = elasticsearch_id

                    aid.save()
                else:

                    # Update an existing entry
                    record = {'doc':{'id': id, 'type': aid.aid_type, 'title': aid.title, 'repository': aid.repository, 'content': aid.scope_and_content, 'source': source_url, 'destination': ""}}
                    json_record = json.dumps(record)

                    es.update(id=aid.elasticsearch_id, index='nafan', doc_type='_doc', body=json_record)

            except Exception as ex:
                print('Error in indexing data')
                print(str(ex))

        except Exception as e:
            print("Unable to process the " + filepath + " file " + str(e))
            response = "Unable to process the " + filepath + " file " + str(e)

        return response

    def parse_did(soup, aid, component_level):

        # There is a situation where the parsing of a <cXX> component can pick up the elements
        # associated with a child of the component since the child's elements are included in the
        # tag pickup

        # One way to possibly deal with this is to make sure the item's level matches the expected
        # level, meaning if we are parsing <c01> and the parent of an element is <c02>, we don't want
        # the data for that tag

        # ToDo: There are assignments in place that assign a string from an element.  If there is a subfield
        # within the string, the assignment is crashing.  For example some of the abstract elements in components
        # of syr-wayland-smith_p.xml in the eaddiva files.

        did = soup.find('did')
        if not did:
            did = soup

        aid.level = component_level

        title = did.find('unittitle')
        if FindingAid.legit_component(title, component_level):
            aid.title = title.string

        try:
            if not aid.title:
                if title:
                    searched_title = title.next
                    if searched_title:
                        aid.title = searched_title.string

            if not aid.title:
                subtitle = title.find('title')
                if subtitle:
                    aid.title = subtitle.string

        except Exception as ex:
            print('Error getting title')
            print(str(ex))

        if not aid.title:
            aid.title = "No title"
        
        dates = did.find_all('unitdate') 
        for date in dates: 
            if date.has_attr('type'):
                attribute = date['type']
                if attribute == "bulk":
                    aid.date = aid.date + " [bulk " + date.string + "]"   
                else:
                    aid.date = aid.date + " " + date.string
            else:
                aid.date = date.string
        if aid.date:
            aid.date = aid.date.strip()    

        containers = did.find_all('container') 
        for container in containers:
            if container.has_attr('type'):
                aid.container = aid.container + container['type']
            if container.string:
                aid.container = aid.container + " " + container.string + " "   

        repository = did.find('repository')
        if FindingAid.legit_component(repository, component_level):
            corpname = repository.find('corpname')
            if corpname:
                aid.intra_repository = corpname.string
            else:
                aid.intra_repository = ""

        reference_codes = did.find_all('unitid') 
        for entry in reference_codes:
            aid.reference_code = aid.reference_code + entry.string + "; "

        # Multiple creators looks a little weird with this technique
        creator = did.find_all('origination') 
        if creator:
            for entry in creator:
                aid.creator = aid.creator + entry.get_text() + " "
            aid.creator = cleanhtml(str(aid.creator))
            aid.creator = aid.creator.strip()

        # Using this technique smashes words together from different tags
        # Found this
        #   <container type="box" label="Box ">1 </container>
        # physdesc = did.find('physdesc')
        # if physdesc:
        #     aid.extent = physdesc.get_text()
        #     aid.extent = cleanhtml(str(aid.extent))

        physdescs = did.find_all('extent') 
        for entry in physdescs:
            aid.extent = aid.extent + entry.string + "; "

        aid.abstract = String_or_p_tag(did, 'abstract')

        # abstract = did.find('abstract')
        # if abstract:
        #     aid.abstract = abstract.string

        # if not aid.abstract:
        #     searched_abstract = abstract.next
        #     if searched_abstract:
        #         aid.abstract = searched_abstract.string

        # First see if langmaterial has text
        languages = did.find_all('langmaterial')
        for lang in languages:
            aid.languages = aid.languages  + " " + lang.get_text()

        # If there is no langmaterial text, look for languages
        aid.languages = aid.languages.strip()
        if not aid.languages:
            languages = did.find_all('language')
            for lang in languages:
                if lang.string:
                    aid.languages = aid.languages + " " + lang.string 
                else:
                    # If no language text, pull the langcode
                    aid.languages = lang['langcode']

        # Although the following are not necessarily in the high did, they are here because
        # they may be contained in a <cXX>

        # There can be multiple accessrestrict entries
        aid.governing_access = String_or_p_tag(did, 'accessrestrict')
        # governing_access = did.find_all('accessrestrict') 
        # if governing_access:
        #     for entry in governing_access:
        #         aid.governing_access = aid.governing_access + entry.get_text() + " "
        #     aid.governing_access = cleanhtml(str(aid.governing_access))
        #     aid.governing_access = aid.governing_access.strip()

        aid.rights = String_or_p_tag(did, 'userestrict')
        aid.citation = String_no_p_tag(did, 'prefercite')

        aid.bioghist = String_or_p_tag(did, 'bioghist')
        aid.scope_and_content = String_or_p_tag(did, 'scopecontent')
        aid.originals_location = String_or_p_tag(did, 'originalsloc')
        aid.note = String_or_p_tag(did, 'note')

        return aid

    def legit_component(component, component_level):

        if not component:
            return False

        component_parent = component.parent
        if component_parent.name == "did":
            component_parent = component_parent.parent

        if component_parent.name == component_level:
            return True

        return False

    def process_components(real_soup, soup, progenitorID, parentID, component_level):

        # Process this level
        current_level = ""
        if component_level < 10:
            current_level = "c0" + str(component_level)
        else:
            current_level = "c" + str(component_level)

        aid = FindingAid()

        # did = soup.find('did')
        # if did:
        #     aid = FindingAid.ParseDid(did, aid, current_level)
        # else:
        aid = FindingAid.ParseDid(soup, aid, current_level)

        if not aid.scope_and_content:
            # aid.scope_and_content = String_or_p_tag(soup, 'scopecontent')

                entries = soup.find_all('scopecontent')
                if entries:
                    entry = entries[0]

                    # finding tag whose child to be deleted
                    div_bs4 = entry.find('head')
                    
                    # delete the child element
                    if div_bs4:
                        div_bs4.clear()

                    element = entry.find('title')
                    if element:
                        new_tag = real_soup.new_tag("i")
                        new_tag.string = element.string
                        element.replace_with(new_tag)

                    aid.scope_and_content = str(entry)

        aid.progenitorID = progenitorID
        aid.parentID = parentID
        aid.component = current_level

        for x in range(1, component_level):
            aid.indent = aid.indent + "&nbsp;&nbsp;"

        aid.save()

        # Process the children
        component_level = component_level + 1

        if component_level < 10:
            search_for = "c0" + str(component_level)
        else:
            search_for = "c" + str(component_level)

        components = soup.find_all(search_for)
        for component in components:
            # did = component.find('did')
            # if did:
            #     FindingAid.ProcessComponents(did, progenitorID, aid.pk, component_level)
            # else:
                FindingAid.ProcessComponents(real_soup, component, progenitorID, aid.pk, component_level)
    
class ControlAccess(models.Model):
    finding_aid = models.ForeignKey('FindingAid', on_delete=models.CASCADE)
    term = models.CharField(max_length=255, blank=True)
    link = models.CharField(max_length=1255, blank=True)
    control_type = models.CharField(max_length=1255, blank=True)

# Audits of Finding Aid creation and modification
class FindingAidAudit(models.Model):
    finding_aid = models.ForeignKey('FindingAid', on_delete=models.CASCADE)
    revision_notes = models.CharField(max_length=255, blank=True)
    update_date = models.DateField(null=True)
    updated_by = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.revision_notes

class Chronology(models.Model):
    finding_aid = models.ForeignKey('FindingAid', on_delete=models.CASCADE)
    date = models.CharField(max_length=255, blank=True)
    event = models.CharField(max_length=1255, blank=True)
    sort_order = models.IntegerField()

# Used to add Subject Headers for a finding aid to be used with searches.  These have not been added to
# the Elasticsearch functionality.  I believe the desired implementation is to have them as available values
# per repository and then make them available to select at the finding aid level.
class SubjectHeader(models.Model):
    finding_aid = models.ForeignKey('FindingAid', on_delete=models.CASCADE)
    subject_header = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.subject_header

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  cleantext = cleantext.replace("\r","")
  cleantext = cleantext.replace("\t","")
  cleantext = cleantext.replace("\n","")
  cleantext = cleantext.replace("'\n',","")
  cleantext = cleantext.replace("'\\n'"," ")

  return cleantext

def strip_p(text):
  cleantext = text.replace("<p>","")
  cleantext = text.replace("</p>","")

  return cleantext

def String_or_p_tag(soup, tag):

    # Need to consider multiple <p> tags within a tag

    response = ""
    element = soup.find(tag)
    if element:

        div_bs4 = element.find('head')
                
        # # delete the child element
        if div_bs4:
            div_bs4.clear()

        response = element.string

        # If the return_value is blank, see if they put in a <p> entries
        if not response:
            response = str(element)

        response = element.get_text()

    if not response:
        response = ""

    return response

def String_no_p_tag(soup, tag):

    # Need to consider multiple <p> tags within a tag

    response = ""
    element = soup.find(tag)
    if element:
        response = element.string

        # If the return_value is blank, see if they put in a <p> entries
        if not response:
            response = element.p.string

    if not response:
        response = ""

    return response


# Subject headers
