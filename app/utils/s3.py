from django.conf import settings 
import logging 
logger = logging.getLogger('S3Utility')

MAX_EXPIRATION_ONE_WEEK_SECS = 604800
def update_private_s3_image_url(page_object):
    """ Update the prviate s3 image URL for a given page object (this expires, 
    needs to be reset occassionally; happens when you open multiview if necessary) """
    logger.info(f'Updating private S3 image URL for page {page_object.id}')
    try:
        page_object.s3_private_image_url = settings.S3_CLIENT.generate_presigned_url('get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': page_object.get_filepath()
                },
            ExpiresIn=MAX_EXPIRATION_ONE_WEEK_SECS
            )
        page_object.save()
    except Exception as e:
        logger.error(e)

def update_private_s3_image_urls_all_pages_for_doc(pages=[]):
    from ..models import Page 
    for p in pages:
        update_private_s3_image_url(page_object=p)