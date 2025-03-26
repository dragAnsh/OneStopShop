import os
from cloudinary.uploader import upload
from django.core.management.base import BaseCommand
from store.models import Product
import cloudinary

cloudinary.config( 
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),  
  api_key = os.environ.get("CLOUDINARY_API_KEY"),  
  api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

class Command(BaseCommand):
    help = 'Bulk upload product images'

    def handle(self, *args, **kwargs):
        image_dir = 'media/uploads/product/'

        for filename in os.listdir(image_dir):
            if filename.endswith(('.webp')):  # Ensure image files only
                product_name = os.path.splitext(filename)[0]
                product_name = product_name.replace("_", " ")
                print(product_name)

                try:
                    product = Product.objects.get(name__iexact=product_name)
                    image_path = os.path.join(image_dir, filename)

                    # Upload to Cloudinary
                    cloudinary_response = upload(image_path)

                    # Save Cloudinary image URL to Product
                    product.image = cloudinary_response['url']
                    product.save()

                    self.stdout.write(self.style.SUCCESS(f'Successfully uploaded: {filename}'))
                except Product.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'No matching product for: {filename}'))