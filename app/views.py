'''
from django.shortcuts import render
from pptx import Presentation


# Create your views here.
from django.http import HttpResponse

def index(request):
	prs = Presentation('app/test.pptx')
	for slide in prs.slides:
		for shape in slide.shapes:
			if shape.has_text_frame:
				return HttpResponse(shape.text)
	return HttpResponse("No titles")
	''
	slides = prs.slides
	slide = slides[0]
	res = slide.title
	#return HttpResponse(slide.name)
	if res != None:
		return HttpResponse(res)
	else:
		return HttpResponse("No response")
	''
'''

import requests
from mimetypes import MimeTypes
from .utils import DriveAPI


from django.shortcuts import redirect
from django.http import HttpResponse, FileResponse


def display_document(request):
    # Use credentials for whatever
    obj = DriveAPI()

    print("Attempting file download")

    # TODO: parameterize these so they aren't hardcoded

    # Change this if you want to change the id of the document that's being downloaded
    f_id = "1jN3sdlIlTy2W1Ce9OAxpie0vDJZUfOGK1MUKtlIlvuk"

    # This is the file that will be used to store the pdf version of the document on google drive
    f_name = "test_download.pdf"

    obj.FileDownload(f_id, f_name)
    try:
        return FileResponse(open(f_name, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404()

def say_hello(request):
    return HttpResponse('Hello')
