from django.core.management.base import BaseCommand
from django.db import transaction
from delivery.models import DeliveryPincode, DeliverySettings

# PIN-to-locality reference dataset bundled with this command.
# PIN codes are postal delivery areas, not precise geofenced service boundaries.
PIN_AREAS = {'560001': 'Bengaluru GPO / MG Road', '560002': 'Bengaluru City', '560003': 'Malleswaram', '560004': 'Basavanagudi', '560005': 'Frazer Town', '560006': 'Benson Town', '560007': 'Agram', '560008': 'HAL / Cambridge Layout', '560009': 'KG Road', '560010': 'Rajajinagar', '560011': 'Jayanagar 3rd Block', '560012': 'IISc', '560013': 'Jalahalli', '560015': 'Jalahalli West', '560016': 'Ramamurthy Nagar / Dooravani Nagar', '560017': 'Vimanapura', '560018': 'Chamarajpet', '560020': 'Seshadripuram', '560021': 'Srirampuram', '560022': 'Yeshwanthpur', '560023': 'Magadi Road', '560024': 'Hebbal Kempapura', '560025': 'Richmond Town', '560026': 'Nayandahalli', '560027': 'Shantinagar / Wilson Garden', '560029': 'Tavarekere', '560030': 'Adugodi', '560032': 'RT Nagar', '560033': 'Maruthi Sevanagar', '560034': 'Koramangala', '560035': 'Carmelaram', '560036': 'KR Puram', '560037': 'Marathahalli / Kundalahalli', '560038': 'Indiranagar', '560040': 'Vijayanagar', '560041': 'Jayanagar', '560042': 'Ulsoor', '560043': 'Banaswadi', '560045': 'Arabic College', '560047': 'Austin Town', '560048': 'Mahadevapura', '560049': 'Bhattarahalli / Avalahalli', '560050': 'Banashankari', '560051': 'Shivajinagar', '560052': 'Vasanth Nagar', '560053': 'Chickpet', '560054': 'Mathikere', '560055': 'Malleswaram West', '560056': 'Bangalore University / Jnanabharathi', '560057': 'Peenya', '560058': 'Peenya Industrial Area', '560059': 'RV College / Mysore Road', '560060': 'Kengeri', '560061': 'Subramanyapura', '560062': 'Doddakallasandra', '560063': 'Yelahanka', '560064': 'Yelahanka New Town', '560065': 'GKVK', '560066': 'Whitefield', '560067': 'Kadugodi', '560068': 'Bommanahalli', '560070': 'Banashankari 2nd Stage', '560071': 'Domlur', '560072': 'Nagarbhavi', '560073': 'Nagasandra', '560074': 'Kumbalgodu', '560075': 'New Thippasandra', '560076': 'BTM Layout / Bannerghatta Road', '560077': 'Kothanur / Hennur', '560078': 'JP Nagar', '560079': 'Basaveshwaranagar', '560080': 'Sadashivanagar', '560082': 'Uttarahalli / Kagalipura', '560083': 'Bannerghatta / Gottigere', '560084': 'Lingarajapuram', '560085': 'Banashankari 3rd Stage', '560086': 'Mahalakshmipuram', '560087': 'Varthur', '560088': 'Hesaraghatta', '560090': 'Abbigere', '560091': 'Vishwaneedam', '560092': 'Sahakara Nagar', '560093': 'CV Raman Nagar', '560094': 'RMV 2nd Stage', '560095': 'Koramangala 6th Block', '560096': 'Nandini Layout', '560097': 'Vidyaranyapura', '560098': 'Rajarajeshwari Nagar', '560099': 'Bommasandra', '560100': 'Electronic City', '560102': 'HSR Layout', '560103': 'Bellandur', '560104': 'Nagarbhavi 2nd Stage', '560105': 'Anjanapura', '560109': 'Thalaghattapura', '560110': 'Ullal', '562106': 'Anekal', '562107': 'Attibele', '562109': 'Bidadi', '562110': 'Devanahalli', '562114': 'Hoskote', '562123': 'Nelamangala', '562125': 'Sarjapura', '562130': 'Tavarekere (Bengaluru)', '562149': 'Bagalur', '562157': 'Bettahalasuru', '562162': 'Madanayakanahalli'}

class Command(BaseCommand):
    help = "Seed Bengaluru and nearby delivery PINs. Existing admin edits are preserved."

    def add_arguments(self, parser):
        parser.add_argument('--update-existing', action='store_true', help='Update locality labels of existing records (never changes serviceability or COD flags).')

    @transaction.atomic
    def handle(self, *args, **options):
        settings, created = DeliverySettings.objects.get_or_create(pk=1, defaults={
            'enabled': True, 'cod_enabled': True, 'allow_all_india': False,
            'estimated_min_days': 3, 'estimated_max_days': 7,
            'notice': 'Delivery estimate is indicative and confirmed at checkout.'
        })
        if not settings.enabled:
            self.stdout.write(self.style.WARNING('DeliverySettings is disabled; enable it in Django Admin if you intend to accept orders.'))
        if settings.allow_all_india:
            self.stdout.write(self.style.WARNING('allow_all_india is ON; switch it OFF in Django Admin for PIN-restricted delivery.'))
        added=0
        for pin, place in PIN_AREAS.items():
            obj, new = DeliveryPincode.objects.get_or_create(pincode=pin, defaults={
                'city': place, 'state': 'Karnataka', 'is_serviceable': True,
                'cod_available': True, 'min_days': 3, 'max_days': 7,
            })
            if new:
                added+=1
            elif options['update_existing']:
                obj.city=place;obj.state='Karnataka';obj.save(update_fields=['city','state'])
        self.stdout.write(self.style.SUCCESS(f'Seeded {added} new delivery PINs; {len(PIN_AREAS)} total in seed. Existing serviceability, COD and timing settings were not overwritten.'))
