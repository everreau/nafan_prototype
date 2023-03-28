from django.core.management.base import BaseCommand

from core.models import Repository, RepositoryType

import csv

class Command(BaseCommand):
    """Import repositories"""
    help = "import repositories"

    def add_arguments(self, parser):
        parser.add_argument(
            "import_file", help="filename to import", type=str
        )

    def handle(self, *args, **options):
        import_file = options.get("import_file")

        Repository.objects.all().delete()

        with open(import_file, newline='', encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0

            for row in reader:
                aname = row['repository_name_authorized']
                name = aname if aname else row['repository_name_unauthorized'].replace('\n', ' ')
                print(f'{name}\t{row["id"]}\t{row["repository_type"]}\t')
                repo = Repository.objects.create(name=name, 
                                                 slug=row['id'],
                                                 status=Repository.UNVERIFIED)
                repo.repository_type, created = RepositoryType.objects.get_or_create(name=row["repository_type"])

                repo.street_address_1 = row['street_address_1']
                repo.street_address_2 = row['street_address_2']
                repo.po_box = row['po_box']
                repo.st_city = row['st_city']
                repo.st_zip_code_5_numbers = row['st_zip_code_5_numbers']
                repo.st_zip_code_4_following_numbers = row['st_zip_code_4_following_numbers']
                repo.street_address_county = row['street_address_county']
                repo.state = row['state']

                repo.url = row['url']

                repo.latitude = row['latitude']
                repo.longitude = row['longitude']

                repo.notes = row['notes']

                repo.save()
                count += 1
            
            print(f'Found {count} repositories')
            