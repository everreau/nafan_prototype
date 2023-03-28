from django.core.management.base import BaseCommand

from core.models import Repository

import csv

HEADERS = ['id',
           'repository_name_unauthorized', 
           'name_notes', 
           'parent_org_unauthorized', 
           'repository_name_authorized',
           'repository_identifier_authorized', 
           'repository_type', 
           'location_type', 
           'street_address_1', 
           'street_address_2', 
           'po_box',
            'st_city', 
            'st_zip_code_5_numbers', 
            'st_zip_code_4_following_numbers', 
            'street_address_county', 
            'po box', 
            'state',
            'email',
            'phone',
            'status', 
            'description',
            'url', 
            'latitude', 
            'longitude', 
            'language_of_entry', 
            'date_entry_recorded', 
            'entry_recorded_by', 
            'source_of_repository_data',
            'url_of_source_of_repository_data', 
            'notes', 
            'geocode_confidence']

class Command(BaseCommand):
    """Export repositories"""
    help = "Export repositories"

    def add_arguments(self, parser):
        parser.add_argument(
            "export_file", help="filename to export", type=str
        )

    def handle(self, *args, **options):
        export_file = options.get("export_file")

        results = Repository.objects.all().order_by('repository_name')

        try:
            export_file = csv.writer(open(export_file, 'w', newline='', encoding="utf8"))
            export_file.writerow(HEADERS)

            for r in results.iterator():
                export_file.writerow([r.id, 
                                      r.repository_name, 
                                      r.name_notes, 
                                      r.parent_organization, 
                                      r.repository_name_authorized,
                                      r.repository_identifier_authorized, 
                                      r.repository_type,
                                      r.location_type,
                                      r.street_address_1, 
                                      r.street_address_2, 
                                      r.po_box,
                                      r.st_city,
                                      r.st_zip_code_5_numbers, 
                                      r.st_zip_code_4_following_numbers, 
                                      r.street_address_county, 
                                      r.po_box, 
                                      r.state,
                                      r.email, 
                                      r.phone, 
                                      r.status, 
                                      r.description,
                                      r.url, 
                                      r.latitude, 
                                      r.longitude, 
                                      r.language_of_entry, 
                                      r.date_entry_recorded, 
                                      r.entry_recorded_by, 
                                      r.source_of_repository_data,
                                      r.url_of_source_of_repository_data,
                                      r.notes, 
                                      r.geocode_confidence])

        except Exception as e:
            print(e)
