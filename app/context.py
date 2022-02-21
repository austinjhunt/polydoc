def theme_context(request):
    if 'theme' in request.session:
        theme = request.session['theme']
    else: 
        theme = "light-theme"
    return {'theme': theme}