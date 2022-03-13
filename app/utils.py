def clean_and_shorten_filename(filename): 
    # Shorten filename if longer than 15 chars. Otherwise it causes problems.
    _extension = filename.split('.')[-1] 
    end_index = min(15, len(filename)-(len(_extension) + 1))
    filename = f'{filename[:end_index]}.{_extension}'
    return filename.replace(' ','-').strip().lower()