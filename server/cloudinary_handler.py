import cloudinary
import cloudinary.uploader
import cloudinary.utils
import os

class CloudinaryHandler:
    def __init__(self):
        cloudinary.config(
            cloud_name='dkozkdqen',
            api_key='951586527394119',
            api_secret=os.environ.get('CLOUDINARY_API'),
            secure=True
        )

    def upload_image(self, img_bytes_io, public_id):
        cloudinary.uploader.upload(
            img_bytes_io,
            public_id=public_id,
            overwrite=True,
            invalidate=True
        )

        url, options = cloudinary.utils.cloudinary_url(
            public_id,
            secure=True,
            version=None
        )
        return url
    
    def destroy_image(self, public_id):
        result = cloudinary.uploader.destroy(public_id, invalidate=True)
        return result

