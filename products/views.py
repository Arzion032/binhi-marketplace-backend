from PIL import Image
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsFarmer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import models
from django.shortcuts import get_object_or_404
from .models import Product, Category, ProductImage, Review, ProductVariation,VariationImage
from .serializers import ProductDetailSerializer, ProductSerializer, ProductReviewSerializer, ProductVariationSerializer, LandingProductSerializer
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.uploadedfile import InMemoryUploadedFile
import json, io, uuid
from django.core.exceptions import ValidationError

def validate_uuid_list(uuid_list):
    valid_uuids = []
    for item in uuid_list:
        try:
            # Attempt to convert each item to a valid UUID
            valid_uuids.append(str(uuid.UUID(item)))  # str() to avoid any format issues
        except ValueError:
            # If conversion fails, skip the invalid UUID
            continue
    return valid_uuids


class ProductDetailView(APIView):
    def get(self, request, slug):
        # Fetch the product with select_related and prefetch_related for optimization
        product = get_object_or_404(
            Product.objects.select_related('category').prefetch_related('images', 'variations', 'reviews'),
            slug=slug
        )

        # Get product reviews
        reviews_qs = product.reviews.all()

        # Get related products (same category, excluding itself)
        related_qs = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

        # Serialize all parts
        product_data = ProductSerializer(product).data
        reviews_data = ProductReviewSerializer(reviews_qs, many=True).data
        related_data = LandingProductSerializer(related_qs, many=True).data

        response_data = {
            'product': product_data,
            'reviews': reviews_data,
            'related_products': related_data
        }

        # Return the response
        return Response(response_data)
    

class CreateProductView(APIView):
    permission_classes = [IsAuthenticated, IsFarmer]

    def post(self, request):
        product_data = request.data.copy()
        product_data['vendor'] = request.user.id
        product_data['status'] = 'hidden'

        # Parse variations from JSON string
        variations_json = product_data.get('variations')
        try:
            variations = json.loads(variations_json) if variations_json else []
        except json.JSONDecodeError:
            return Response({'error': 'Invalid variations JSON'}, status=status.HTTP_400_BAD_REQUEST)

        product_data.pop('variations', None)

        # Serialize and save product
        serializer = ProductSerializer(data=product_data)
        if serializer.is_valid():
            product = serializer.save()

            # Handle image uploads and set main image
            images = request.FILES.getlist('images')
            has_main = False
            for img in images:
                
                if img.size > 5 * 1024 * 1024:  # 5MB size limit
                    return Response({"error": "Each image must be <5MB."}, status=400)

                # Open the image
                image = Image.open(img)

                # If the image has transparency (RGBA), convert it to RGB or save as PNG if required
                if image.mode == 'RGBA':
                    # Save it as PNG to preserve transparency
                    image_io = io.BytesIO()
                    image.save(image_io, format='PNG')  # Save as PNG to preserve transparency
                    image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/png', image_io.tell(), None)
                else:
                    # If it's not RGBA, just save it as JPEG
                    image_io = io.BytesIO()
                    image.save(image_io, format='JPEG')  # Save as JPEG if no transparency
                    image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/jpeg', image_io.tell(), None)

                # Check if the image should be marked as main (via 'is_main' field or first image logic)
                is_main = request.data.get(f'{img.name}_is_main', False)  # Check for 'is_main' flag per image
                if not has_main and (is_main == 'true' or is_main is True):  # Set as main if provided
                    has_main = True

                # Create the ProductImage (you might use ProductImageSerializer to validate)
                product_image = ProductImage.objects.create(product=product, image_file=image_file, is_main=is_main)

            # If no main image is set, automatically set the first image as the main one
            if images and not has_main:
                first_image = ProductImage.objects.filter(product=product).first()
                if first_image:
                    first_image.is_main = True
                    first_image.save()

            # Handle variations (if you have a separate view for variations, you may skip this part)
            for variation_data in variations:
                variation_serializer = ProductVariationSerializer(data=variation_data)
                if variation_serializer.is_valid():
                    variation_serializer.save(product=product)
                else:
                    return Response({
                        'error': 'Invalid variation data',
                        'details': variation_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProductView(APIView):
    permission_classes = [IsAuthenticated, IsFarmer]  # Replace IsFarmer as needed
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        product_data = request.data.copy()
        new_images = request.FILES.getlist('images')

        with transaction.atomic():
            # 1. Update product fields
            serializer = ProductSerializer(product, data=product_data, partial=True)
            if serializer.is_valid():
                product = serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # 2. Handle image deletion
            images_to_delete_raw = request.data.get('images_to_delete')
            print("RAW images_to_delete:", images_to_delete_raw, type(images_to_delete_raw))

            try:
                images_to_delete = json.loads(images_to_delete_raw) if images_to_delete_raw else []
            except Exception as e:
                print("JSON parse error:", e)
                images_to_delete = []
            print("After json.loads:", images_to_delete, type(images_to_delete))

            if isinstance(images_to_delete, list) and images_to_delete:
                valid_image_ids = []
                for img_id in images_to_delete:
                    try:
                        valid_image_ids.append(uuid.UUID(str(img_id)))
                    except Exception as e:
                        print(f"Invalid UUID in images_to_delete: {img_id}, error: {e}")
                print("UUID objects for deletion:", valid_image_ids)
                if valid_image_ids:
                    deleted_count, _ = ProductImage.objects.filter(
                        id__in=valid_image_ids,
                        product_id=product.id
                    ).delete()
                    print(f"Deleted {deleted_count} ProductImage(s)")
                else:
                    print("No valid UUIDs to delete.")
            else:
                print("images_to_delete is not a list or is empty.")

            # 3. Handle image uploads
            for img in new_images:
                # Optional: Restrict large images (e.g., 5MB limit)
                if img.size > 5 * 1024 * 1024:  # 5MB size limit
                    return Response({"error": "Each image must be <5MB."}, status=400)

                image = Image.open(img)
                if image.mode == 'RGBA':
                    image_io = io.BytesIO()
                    image.save(image_io, format='PNG')
                    image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/png', image_io.tell(), None)
                else:
                    image_io = io.BytesIO()
                    image.save(image_io, format='JPEG')
                    image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/jpeg', image_io.tell(), None)

                is_main = request.data.get(f'{img.name}_is_main', False)

                # Normalize input (e.g., if it's a string like 'true')
                if is_main == 'true':
                    is_main = True
                ProductImage.objects.create(product=product, image_file=image_file, is_main=is_main)

               
                # Check for existing images and if any are already marked as main
        has_main_image = ProductImage.objects.filter(product=product, is_main=True).exists()

            # If images exist but no image is set as main, promote the first one
        if not has_main_image:
            first_image = ProductImage.objects.filter(product_id=product).first()
            if first_image:
                first_image.is_main = True
                print(first_image.is_main)
                first_image.save()

        return Response(ProductSerializer(product).data, status=status.HTTP_200_OK)

class DeleteProductView(APIView):
    def delete(self, request, slug):
        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response({'message': f'Product {product.name} deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    
    
class CreateVariationView(APIView):
    permission_classes = [IsAuthenticated, IsFarmer]  # Add/replace IsFarmer as needed
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            # 1. Extract basic fields (product is required)
            product_id = request.data.get('product')
            if not product_id:
                return Response({"error": "Product is required."}, status=400)

            variation_data = {
                'product': product_id,
                'name': request.data.get('name', ''),
                'unit_price': request.data.get('unit_price'),
                'stock': request.data.get('stock'),
                'is_available': request.data.get('is_available', True),
                'is_default': request.data.get('is_default', False),
            }

            # 2. Create variation
            variation_serializer = ProductVariationSerializer(data=variation_data)
            if not variation_serializer.is_valid():
                return Response(variation_serializer.errors, status=400)
            variation = variation_serializer.save()
            
            # 2.5 Check if the product has only one variation and no default variation set
            product_variations = ProductVariation.objects.filter(product=product_id)
            
            if product_variations.count() == 1 and not product_variations.filter(is_default=True).exists():
                # 4. If this is the only variation and no default exists, set it as default
                variation.is_default = True
                variation.save()

            # 3. Handle images (if any)
            images = request.FILES.getlist('images')
            has_main = False
            for img in images:
                
                if img.size > 5 * 1024 * 1024:  # 5MB size limit
                    return Response({"error": "Each image must be <5MB."}, status=400)

                # Open the image
                image = Image.open(img)

                # If the image has transparency (RGBA), convert it to RGB or save as PNG if required
                if image.mode == 'RGBA':
                    # Save it as PNG to preserve transparency
                    image_io = io.BytesIO()
                    image.save(image_io, format='PNG')  # Save as PNG to preserve transparency
                    image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/png', image_io.tell(), None)
                else:
                    # If it's not RGBA, just save it as JPEG
                    image_io = io.BytesIO()
                    image.save(image_io, format='JPEG')  # Save as JPEG if no transparency
                    image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/jpeg', image_io.tell(), None)

                # Check if the image should be marked as main (via 'is_main' field or first image logic)
                is_main = request.data.get(f'{img.name}_is_main', False)  # Check for 'is_main' flag per image
                if not has_main and (is_main == 'true' or is_main is True):  # Set as main if provided
                    has_main = True
                    
                VariationImage.objects.create(
                    variation=variation,
                    image_file=img,
                    is_main=is_main == 'true' or is_main is True
                )

            # If no main is set but images exist, set first as main
            if images and not has_main:
                first_image = VariationImage.objects.filter(variation=variation).first()
                if first_image:
                    first_image.is_main = True
                    first_image.save()

            return Response(ProductVariationSerializer(variation).data, status=status.HTTP_201_CREATED)
    
class UpdateVariationView(APIView):
        permission_classes = [IsAuthenticated, IsFarmer]  # Add/replace IsFarmer as needed
        parser_classes = [MultiPartParser, FormParser]

        def patch(self, request, uuid):
            variation = get_object_or_404(ProductVariation, id=uuid)
            data = request.data.copy()

            # Collect new images and images to delete
            new_images = request.FILES.getlist('images')
            images_to_delete = request.data.getlist('images_to_delete', [])

            with transaction.atomic():
                # 1. Update variation fields (partial)
                serializer = ProductVariationSerializer(variation, data=data, partial=True)
                if serializer.is_valid():
                    variation = serializer.save()
                else:
                    return Response(serializer.errors, status=400)

                # 2. Delete requested images
                if images_to_delete:
                    VariationImage.objects.filter(id__in=images_to_delete, variation=variation).delete()

                # 3. Add new images and handle is_main logic
                for img in new_images:
                    if img.size > 5 * 1024 * 1024:
                        return Response({"error": "Each image must be <5MB."}, status=400)

                    image = Image.open(img)
                    if image.mode == 'RGBA':
                        image_io = io.BytesIO()
                        image.save(image_io, format='PNG')
                        image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/png', image_io.tell(), None)
                    else:
                        image_io = io.BytesIO()
                        image.save(image_io, format='JPEG')
                        image_file = InMemoryUploadedFile(image_io, None, img.name, 'image/jpeg', image_io.tell(), None)

                    is_main = request.data.get(f"{img.name}_is_main", False)
                    is_main = is_main == 'true' or is_main is True

                    VariationImage.objects.create(
                        variation=variation,
                        image_file=image_file,  # Use correct field
                        is_main=is_main
                    )

            # 4. Enforce only one main image per variation
            main_images = VariationImage.objects.filter(variation=variation, is_main=True)
            if main_images.count() > 1:
                # Keep only the most recent as main, demote others
                to_keep = main_images.latest('uploaded_at')
                main_images.exclude(id=to_keep.id).update(is_main=False)

            # 5. If there are images and none is main, set first as main
            if VariationImage.objects.filter(variation=variation).exists() and not VariationImage.objects.filter(variation=variation, is_main=True).exists():
                first_img = VariationImage.objects.filter(variation=variation).first()
                first_img.is_main = True
                first_img.save()

            return Response(ProductVariationSerializer(variation).data, status=status.HTTP_200_OK)

class DeleteVariationView(APIView):
    permission_classes = [IsAuthenticated, IsFarmer]  # your custom permission

    def delete(self, request, uuid):
        variation = get_object_or_404(ProductVariation, id=uuid)
        variation.delete()
        return Response({"detail": f"Variation {variation.name} deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class GetAllProducts(APIView):

    VALID_STATUSES = {
        'published', 'out_of_stock', 'hidden', 'pending_approval', 'rejected'
    }

    def get(self, request):
        user_id = request.query_params.get('user_id')
        status = request.query_params.get('status')

      
        products = Product.objects.all()

        if user_id:
            products = products.filter(vendor__id=user_id)

       
        if status and status in self.VALID_STATUSES:
            products = products.filter(status=status)

        else:
            products = products.filter(status='published')


        print(status)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
class LandingProducts(APIView):

    VALID_STATUSES = {
        'published', 'out_of_stock', 'hidden', 'pending_approval', 'rejected'
    }

    def get(self, request):
        user_id = request.query_params.get('user_id')
        status = request.query_params.get('status')

      
        products = Product.objects.all()

        if user_id:
            products = products.filter(vendor__id=user_id)

       
        if status and status in self.VALID_STATUSES:
            products = products.filter(status=status)

        else:
            products = products.filter(status='published')


        print(status)
        serializer = LandingProductSerializer(products, many=True)
        return Response(serializer.data)