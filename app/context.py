
from app.drive.utils import DriveAPI

def theme_context(request):
    # determine if first request or not
    show_loader = False
    if not 'active' in request.session:
        show_loader = True
        request.session['active'] = True

    if 'theme' in request.session:
        theme = request.session['theme']
    else:
        theme = "light-theme"
    return {'theme': theme, 'show_loader': show_loader, 'drive_authenticated': DriveAPI(request=request).has_valid_creds()}
