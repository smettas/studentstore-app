from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Product
class Command(BaseCommand):
    help = "Populate DEMO stock only, never actual warehouse inventory. Explicit confirmation required."
    def add_arguments(self,parser):
        parser.add_argument("--confirm-demo-only",action="store_true")
        parser.add_argument("--overwrite",action="store_true",help="Also overwrite existing positive stock")
    def handle(self,*args,**options):
        if not options["confirm_demo_only"]:raise CommandError("Add --confirm-demo-only for test inventory; do NOT use for live sales.")
        count=0
        with transaction.atomic():
            for p in Product.objects.order_by("id").only("id","stock"):
                if p.stock and not options["overwrite"]:continue
                p.stock=10+(p.id*37)%41
                p.save(update_fields=["stock"])
                count+=1
        self.stdout.write(self.style.WARNING(f"Assigned TEST quantities to {count} products. Replace with verified physical stock before launch."))
